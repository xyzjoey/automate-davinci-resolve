import itertools
from pathlib import Path
from typing import Iterable

import srt

from ..extended_resolve import davinci_resolve_module
from ..extended_resolve.media_pool_item import MediaPoolItem
from ..extended_resolve.resolve import MediaPoolItemInsertInfo
from ..extended_resolve.textplus import TextPlusComposition, TextPlusSettings
from ..extended_resolve.timecode import Timecode
from ..extended_resolve.timeline import Timeline
from ..extended_resolve.timeline_item import TimelineItem
from ..extended_resolve.track import TrackHandle
from ..resolve_types import PyRemoteComposition, PyRemoteOperator
from ..utils.math import FrameRange
from .constants import GeneratedTrackName, SnapMode
from .errors import UserError
from .smart_edit_bin import SmartEditBin
from .ui.loading_window import LoadingWindow

LineRange = tuple[int, int]


class UniTextPlusControl:
    @classmethod
    def enable_fit_to_textarea(cls, uni_control_tool: PyRemoteOperator):
        out1 = uni_control_tool.TextPlus.GetConnectedOutput()
        textplus = out1.GetTool() if out1 is not None else None

        out2 = uni_control_tool.DataWindowReference.GetConnectedOutput()
        dod_ref = out2.GetTool() if out2 is not None else None

        out3 = uni_control_tool.TextArea.GetConnectedOutput()
        textarea = out3.GetTool() if out3 is not None else None

        if textplus is None or dod_ref is None or textarea is None:
            return

        textarea_width = f"({textplus.Name}.Width * {textarea.Name}.Width)"
        textarea_height = f"({textplus.Name}.Height * {textarea.Name}.Height)"
        dod_width = f"({dod_ref.Name}.Output.DataWindow[3] - {dod_ref.Name}.Output.DataWindow[1])"
        dod_height = f"({dod_ref.Name}.Output.DataWindow[4] - {dod_ref.Name}.Output.DataWindow[2])"

        if textplus.LayoutSize.GetExpression() is None:
            uni_control_tool.SetInput("SavedLayoutSize", textplus.GetInput("LayoutSize"))
        if textplus.LineSizeX.GetExpression() is None:
            uni_control_tool.SetInput("SavedLineSizeX", textplus.GetInput("LineSizeX"))

        textplus.LayoutSize.SetExpression(f"iif({dod_height} ~= 0, {textarea_height} / {dod_height}, 1.0)")
        textplus.LineSizeX.SetExpression(f"iif({dod_width} ~= 0, min(1.0, {textarea_width} * {dod_height} / ({dod_width} * {textarea_height})), 1.0)")

    @classmethod
    def disable_fit_to_textarea(cls, uni_control_tool: PyRemoteOperator):
        out1 = uni_control_tool.TextPlus.GetConnectedOutput()
        textplus = out1.GetTool() if out1 is not None else None

        if textplus is None:
            return

        textplus.LayoutSize.SetExpression()
        textplus.LineSizeX.SetExpression()
        textplus.SetInput("LayoutSize", uni_control_tool.GetInput("SavedLayoutSize"))
        textplus.SetInput("LineSizeX", uni_control_tool.GetInput("SavedLineSizeX"))

    @classmethod
    def reset_resolution(cls, composition: PyRemoteComposition, uni_control_tool: PyRemoteOperator):
        width = composition.GetPrefs("Comp.FrameFormat.Width")
        height = composition.GetPrefs("Comp.FrameFormat.Height")

        out1 = uni_control_tool.TextPlus.GetConnectedOutput()
        textplus = out1.GetTool() if out1 is not None else None

        out2 = uni_control_tool.DataWindowReference.GetConnectedOutput()
        dod_ref = out2.GetTool() if out2 is not None else None

        textplus.SetInput("Width", width)
        textplus.SetInput("Height", height)
        dod_ref.SetInput("Width", width)
        dod_ref.SetInput("Height", height)


class UniTextPlus:
    @classmethod
    def generate_textplus_clips(cls, snap_mode: SnapMode):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()
        media_pool_item = SmartEditBin.get_or_import_uni_textplus()
        active_subtitle_track_handle = next((e for e in timeline.iter_tracks("subtitle") if timeline.get_track_enabled(e)), None)

        if active_subtitle_track_handle is None:
            raise UserError("Failed to find enabled subtitle track")

        subtitle_timeline_items = list(timeline.iter_items_in_track(active_subtitle_track_handle))
        subtitle_ranges = cls._compute_subtitle_insert_ranges(timeline, subtitle_timeline_items, snap_mode)

        track_handle = timeline.get_or_add_track_by_name("video", GeneratedTrackName.TEXT)

        with timeline.rollback_playhead_on_exit():
            old_items = list(timeline.iter_items_in_track(track_handle))
            LoadingWindow.set_message(f"Deleting {len(old_items)} clips...")
            timeline.delete_items(old_items)

            LoadingWindow.set_message(f"Inserting {len(subtitle_ranges)} clips...")
            textplus_timeline_items = resolve.insert_to_timeline(
                [
                    MediaPoolItemInsertInfo(
                        media_pool_item=media_pool_item,
                        start_frame=subtitle_range.start,
                        end_frame=subtitle_range.end,
                        track_handle=track_handle,
                    )
                    for subtitle_range in subtitle_ranges
                ]
            )

            LoadingWindow.set_message(f"Setting {len(textplus_timeline_items)} Text+ content...")
            for textplus_item, subtitle_item in zip(textplus_timeline_items, subtitle_timeline_items):
                textplus_tool = textplus_item._item.GetFusionCompByIndex(1).Template
                textplus_tool.SetInput("StyledText", subtitle_item._item.GetName())

        timeline.set_track_locked(track_handle, True)

    @classmethod
    def copy_style_for_all(cls, source_item: MediaPoolItem):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()
        dst_timeline_items = list(timeline.iter_items(lambda item: cls._is_uni_textplus_clip(item), track_type="video"))

        LoadingWindow.set_message(f"Copying Style to {len(dst_timeline_items)} clips...")
        cls.copy_style_for_clips(dst_timeline_items, source_item)

    @classmethod
    def copy_style_for_track(cls, track_handle: TrackHandle, source_item: MediaPoolItem):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()
        dst_timeline_items = list(timeline.iter_items_in_track(track_handle, lambda item: cls._is_uni_textplus_clip(item)))

        LoadingWindow.set_message(f"Copying Style to {len(dst_timeline_items)} clips at track {track_handle.get_short_name()}...")
        cls.copy_style_for_clips(dst_timeline_items, source_item)

    @classmethod
    def copy_style_for_clip(cls, destinated_item: TimelineItem, source_item: MediaPoolItem):
        cls.copy_style_for_clips([destinated_item], source_item)

    @classmethod
    def copy_style_for_clips(cls, destinated_items: list[TimelineItem], source_item: MediaPoolItem):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()

        with (
            timeline.rollback_playhead_on_exit(),
            resolve.temp_timeline_item(source_item) as src_timeline_item,
        ):
            cls._copy_style(src_timeline_item, destinated_items)

    @classmethod
    def export_srt_for_track(cls, track_handle: TrackHandle, file_path: Path):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()

        LoadingWindow.set_message(f"Collecting subtitle content...")

        subtitle_timeline_items = timeline.iter_items_in_track(track_handle, lambda item: cls._is_uni_textplus_clip(item))
        subtitles = cls._transform_to_subtitles(timeline, subtitle_timeline_items)

        LoadingWindow.set_message(f"Exporting {len(subtitles)} subtitles to file `{file_path}` ...")

        file_content = srt.compose(subtitles)
        file_path.write_text(file_content, encoding="utf-8")

    @classmethod
    def import_srt_for_track(cls, source_timeline_item: TimelineItem, file_path: Path):
        LoadingWindow.set_message(f"Reading srt file `{file_path}`...")

        file_content = file_path.read_text(encoding="utf-8")

        try:
            subtitles = list(srt.parse(file_content))
        except:
            raise UserError(f"Failed to parse srt file `{file_path}`. See console for details.")

        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()
        track_handle = source_timeline_item.get_track_handle()

        src_comp = source_timeline_item._item.GetFusionCompByIndex(1)
        src_tool = src_comp.Template
        src_settings = src_comp.CopySettings(src_tool)

        old_items = list(timeline.iter_items_in_track(track_handle))
        LoadingWindow.set_message(f"Deleting {len(old_items)} clips...")
        timeline.delete_items(old_items)

        media_pool_item = SmartEditBin.get_or_import_uni_textplus()
        if media_pool_item is None:
            raise Exception(f"Failed to import clip `{SmartEditBin.ClipName.UNI_TEXTPLUS}`")

        LoadingWindow.set_message(f"Inserting {len(subtitles)} clips...")
        insert_infos = [
            MediaPoolItemInsertInfo(
                media_pool_item=media_pool_item,
                start_frame=Timecode.from_timedelta(subtitle.start, timeline.get_timecode_settings(), False).get_frame(True),
                end_frame=Timecode.from_timedelta(subtitle.end, timeline.get_timecode_settings(), False).get_frame(True),
                track_handle=track_handle,
            )
            for subtitle in subtitles
        ]
        inserted_items = resolve.insert_to_timeline(insert_infos)

        LoadingWindow.set_message(f"Setting {len(subtitles)} clips content...")
        for i, item in enumerate(inserted_items):
            if item is None:
                raise UserError(f"Failed to insert clip `{SmartEditBin.ClipName.UNI_TEXTPLUS}` with info {insert_infos[i]}")

            tool = item._item.GetFusionCompByIndex(1).Template
            tool.SetInput("StyledText", subtitles[i].content)

        cls._copy_style_from_settings(src_settings, inserted_items)

    @classmethod
    def _transform_to_subtitles(cls, timeline: Timeline, timeline_items: Iterable[TimelineItem]):
        subtitles = []

        for item in timeline_items:
            subtitles.append(
                srt.Subtitle(
                    index=None,
                    start=timeline.get_item_start_timecode(item).get_timedelta(False),
                    end=timeline.get_item_end_timecode(item).get_timedelta(False),
                    content=item._item.GetFusionCompByIndex(1).Template.GetInput("StyledText"),  # TODO: support character level styling
                )
            )

        return subtitles

    @classmethod
    def _is_textplus_clip(cls, item: TimelineItem):
        if item._item.GetFusionCompCount() == 0:
            return False

        comp = item._item.GetFusionCompByIndex(1)

        if comp.Template is None:
            return False

        return comp.Template.GetAttrs("TOOLS_RegID") == "TextPlus"

    @classmethod
    def _is_uni_textplus_clip(cls, item: TimelineItem):
        if item._item.GetFusionCompCount() == 0:
            return False

        comp = item._item.GetFusionCompByIndex(1)

        if comp.UniText is None:
            return False

        return True

    @classmethod
    def _copy_style(cls, src_item: TimelineItem, dst_items: Iterable[TimelineItem]):
        src_comp = TextPlusComposition(src_item._item.GetFusionCompByIndex(1))
        src_settings = src_comp.get_settings("UniTextControl", "TextArea")

        cls._copy_style_from_settings(src_settings, dst_items)

    @classmethod
    def _copy_style_from_settings(cls, src_settings: TextPlusSettings, dst_items: Iterable[TimelineItem]):
        new_settings = src_settings

        for i, dst_item in enumerate(dst_items):
            LoadingWindow.set_message(f"Setting {i + 1}/{len(dst_items)} Text+ content...", dispatch_log=False)

            dst_comp = TextPlusComposition(dst_item._item.GetFusionCompByIndex(1))
            old_settings = dst_comp.get_settings()
            new_textplus_settings = new_settings.get_textplus_tool()
            old_textplus_settings = old_settings.get_textplus_tool()

            new_text = old_settings.get_text_input()._settings["Value"]

            new_settings.get_text_input()._settings["Value"] = new_text
            new_textplus_settings._settings["Inputs"]["GlobalOut"] = old_textplus_settings._settings["Inputs"]["GlobalOut"]

            character_level_settings = new_settings.find_character_level_styling()
            if character_level_settings is not None:
                new_style_array = cls._map_style_array_to_lines(character_level_settings.style_array, new_text)
                character_level_settings.style_array = new_style_array

            dst_comp.set_settings(new_settings)

            new_settings_has_uni_control = new_settings.get_tool("UniTextControl") is not None
            uni_control_tool = dst_comp._composition.UniTextControl

            if not new_settings_has_uni_control and uni_control_tool is not None:
                fit = uni_control_tool.GetInput("FitToTextArea")

                if fit:
                    UniTextPlusControl.enable_fit_to_textarea(uni_control_tool)

    @classmethod
    def _map_style_array_to_lines(cls, style_array: dict, text: str):
        line_ranges: list[LineRange] = sorted({(value[2], value[3]) for value in style_array.values()})
        new_line_ranges = cls._get_line_ranges(text, max_line_count=len(line_ranges) + 1)
        new_style_array = {}

        for i, value in list(style_array.items()):
            line_range = (value[2], value[3])
            line_index = line_ranges.index(line_range)

            if line_index < len(new_line_ranges):
                line_start, line_end = new_line_ranges[line_index]
                value[2] = line_start
                value[3] = line_end
                new_style_array[len(new_style_array) + 1] = value
            else:
                style_array.pop(i)

        return new_style_array

    @classmethod
    def _get_line_ranges(cls, text: str, max_line_count: int) -> list[LineRange]:
        ranges = []
        prev_end = -1

        for i, line in enumerate(text.splitlines()[:max_line_count]):
            start = prev_end + 1

            if i < max_line_count - 1:
                end = start + len(line)
            else:
                end = len(text)

            ranges.append((start, end))
            prev_end = end

        return ranges

    @classmethod
    def _find_text_input(cls, textplus_settings):
        textplus_tool = next((tool for tool in textplus_settings["Tools"].values() if tool["__ctor"] == "TextPlus"))
        character_level_styling_tool = next((tool for tool in textplus_settings["Tools"].values() if tool["__ctor"] == "StyledTextCLS"), None)

        if character_level_styling_tool is not None:
            return character_level_styling_tool["Inputs"]["Text"]
        else:
            return textplus_tool["Inputs"]["StyledText"]

    @classmethod
    def _compute_subtitle_insert_ranges(cls, timeline: Timeline, subtitle_timeline_items: list[TimelineItem], snap_mode: SnapMode):
        subtitle_ranges = [FrameRange(item._item.GetStart(), item._item.GetEnd()) for item in subtitle_timeline_items]

        if not subtitle_ranges or snap_mode == SnapMode.NONE:
            return subtitle_ranges

        snap_target_track_handle = cls._get_audio_track_with_most_clips(timeline)
        snap_target_ranges = [FrameRange(item._item.GetStart(), item._item.GetEnd()) for item in timeline.iter_items_in_track(snap_target_track_handle)]

        return cls._snap_ranges(subtitle_ranges, snap_target_ranges)

    @classmethod
    def _get_audio_track_with_most_clips(cls, timeline: Timeline):
        return sorted(timeline.iter_tracks("audio"), key=lambda t: len(list(timeline.iter_items_in_track(t))), reverse=True)[0]

    @classmethod
    def _snap_ranges(cls, from_ranges: list[FrameRange], to_ranges: list[FrameRange]) -> list[FrameRange]:
        if not to_ranges:
            return from_ranges

        to_ranges = cls._fill_ranges_gap(to_ranges)
        associated_ranges = []

        for from_range in from_ranges:
            to_ranges = list(itertools.dropwhile(lambda to_range: not FrameRange.is_overlapped(from_range, to_range), to_ranges))
            associable_ranges = [
                to_range
                for to_range in itertools.takewhile(lambda to_range: FrameRange.is_overlapped(from_range, to_range), to_ranges)
                if FrameRange.is_overlapped_by_percentage(from_range, to_range)
            ]

            if len(associable_ranges) > 0:
                associated_ranges.append(FrameRange(associable_ranges[0].start, associable_ranges[-1].end))
            else:
                associated_ranges.append(None)

        snapped_ranges = []

        for i, from_range in enumerate(from_ranges):
            associated_range = associated_ranges[i]

            if associated_range is None:
                snapped_ranges.append(from_range)
            else:
                snapped_start = associated_range.start
                snapped_end = associated_range.end

                if i > 0:
                    snapped_start = max(snapped_start, snapped_ranges[-1].end)

                if i < len(from_ranges) - 1:
                    may_overlap_with_next_range = associated_ranges[i + 1] is not None and FrameRange.is_overlapped(associated_range, associated_ranges[i + 1])
                    if may_overlap_with_next_range:
                        snapped_end = min(snapped_end, from_ranges[i + 1].start)

                snapped_ranges.append(FrameRange(snapped_start, snapped_end))

        return snapped_ranges

    @classmethod
    def _fill_ranges_gap(cls, ranges: list[FrameRange]) -> list[FrameRange]:
        filled_ranges = []

        for i, curr_range in enumerate(ranges[:-1]):
            next_range = ranges[i + 1]

            filled_ranges.append(curr_range)

            if next_range.start > curr_range.end:
                filled_ranges.append(FrameRange(curr_range.end, next_range.start))

        filled_ranges += ranges[-1:]

        return filled_ranges
