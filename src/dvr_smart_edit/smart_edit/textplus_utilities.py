import itertools
from pathlib import Path
from typing import Iterable, NamedTuple

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


# class UniTextPlusControl:
#     @classmethod
#     def fit_to_textbox_for_clip(cls, composition: PyRemoteComposition):
#         textplus = composition.Template

#         if textplus is None:
#             return

#         dod = textplus.Output.GetDod()

#         print(dod)

#         # get line direction
#         # get textbox width height
#         # change font size
#         # change line X/Y

#     @classmethod
#     def fit_to_textbox_for_all(cls):
#         pass

#     @classmethod
#     def enable_fit_to_textbox(cls, uni_control_tool: PyRemoteOperator):
#         in1 = uni_control_tool.TextPlus.GetConnectedOutput()
#         textplus = in1.GetTool() if in1 is not None else None

#         in2 = uni_control_tool.DataWindowReference.GetConnectedOutput()
#         dod_ref = in2.GetTool() if in2 is not None else None

#         in3 = uni_control_tool.TextBox.GetConnectedOutput()
#         textbox = in3.GetTool() if in3 is not None else None

#         if textplus is None or dod_ref is None or textbox is None:
#             return

#         textbox_width = f"({textplus.Name}.Width * {textbox.Name}.Width)"
#         textbox_height = f"({textplus.Name}.Height * {textbox.Name}.Height)"
#         dod_width = f"({dod_ref.Name}.Output.DataWindow[3] - {dod_ref.Name}.Output.DataWindow[1])"
#         dod_height = f"({dod_ref.Name}.Output.DataWindow[4] - {dod_ref.Name}.Output.DataWindow[2])"

#         if textplus.LayoutSize.GetExpression() is None:
#             uni_control_tool.SetInput("SavedLayoutSize", textplus.GetInput("LayoutSize"))
#         if textplus.LineSizeX.GetExpression() is None:
#             uni_control_tool.SetInput("SavedLineSizeX", textplus.GetInput("LineSizeX"))

#         textplus.LayoutSize.SetExpression(f"iif({dod_height} ~= 0, {textbox_height} / {dod_height}, 1.0)")
#         textplus.LineSizeX.SetExpression(f"iif({dod_width} ~= 0, min(1.0, {textbox_width} * {dod_height} / ({dod_width} * {textbox_height})), 1.0)")

#     @classmethod
#     def disable_fit_to_textbox(cls, uni_control_tool: PyRemoteOperator):
#         in1 = uni_control_tool.TextPlus.GetConnectedOutput()
#         textplus = in1.GetTool() if in1 is not None else None

#         if textplus is None:
#             return

#         textplus.LayoutSize.SetExpression()
#         textplus.LineSizeX.SetExpression()
#         textplus.SetInput("LayoutSize", uni_control_tool.GetInput("SavedLayoutSize"))
#         textplus.SetInput("LineSizeX", uni_control_tool.GetInput("SavedLineSizeX"))

#     @classmethod
#     def reset_resolution(cls, composition: PyRemoteComposition, uni_control_tool: PyRemoteOperator):
#         width = composition.GetPrefs("Comp.FrameFormat.Width")
#         height = composition.GetPrefs("Comp.FrameFormat.Height")

#         in1 = uni_control_tool.TextPlus.GetConnectedOutput()
#         textplus = in1.GetTool() if in1 is not None else None

#         in2 = uni_control_tool.DataWindowReference.GetConnectedOutput()
#         dod_ref = in2.GetTool() if in2 is not None else None

#         textplus.SetInput("Width", width)
#         textplus.SetInput("Height", height)
#         dod_ref.SetInput("Width", width)
#         dod_ref.SetInput("Height", height)


class SubtitleInfo(NamedTuple):
    content: str
    frame_range: FrameRange


class TextPlusUtilities:
    @classmethod
    def generate_textplus_clips(
        cls,
        subtitle_track_index=None,
        srt_file_path=None,
        snap_mode: SnapMode = SnapMode.NONE,
    ):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()
        media_pool_item = SmartEditBin.get_or_import_textplus()

        if timeline is None:
            raise UserError("No active timeline")

        if subtitle_track_index is not None:
            subtitle_infos = cls._get_subtitle_infos_from_subtitle_track(timeline, subtitle_track_index)
        elif srt_file_path is not None:
            subtitle_infos = cls._get_subtitle_infos_from_srt(timeline, srt_file_path)
        else:
            raise Exception("Missing subtitle source")

        subtitle_ranges = cls._compute_subtitle_insert_ranges(timeline, subtitle_infos, snap_mode)

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
            for textplus_item, subtitle_info in zip(textplus_timeline_items, subtitle_infos):
                comp = textplus_item.get_last_fusion_composition()
                textplus_tool = comp.Template
                textplus_tool.SetInput("StyledText", subtitle_info.content)

        timeline.set_track_locked(track_handle, True)

    @classmethod
    def copy_style_for_all(cls, source_item: MediaPoolItem):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()
        dst_timeline_items = list(timeline.iter_items(lambda item: cls._is_textplus_clip(item), track_type="video"))

        LoadingWindow.set_message(f"Copying Style to {len(dst_timeline_items)} clips...")
        cls.copy_style_for_clips(dst_timeline_items, source_item)

    @classmethod
    def copy_style_for_track(cls, track_handle: TrackHandle, source_item: MediaPoolItem):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()
        dst_timeline_items = list(timeline.iter_items_in_track(track_handle, lambda item: cls._is_textplus_clip(item)))

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

        subtitle_timeline_items = timeline.iter_items_in_track(track_handle, lambda item: cls._is_textplus_clip(item))
        subtitles = cls._transform_to_subtitles(timeline, subtitle_timeline_items)

        LoadingWindow.set_message(f"Exporting {len(subtitles)} subtitles to file `{file_path}` ...")

        file_content = srt.compose(subtitles)
        file_path.write_text(file_content, encoding="utf-8")

    @classmethod
    def fit_textbox_for_clip(cls, timeline_item: TimelineItem):
        if not cls._is_textplus_clip(timeline_item):
            return

        comp = timeline_item.get_last_fusion_composition()
        textplus_tool = comp.Template
        dod = textplus_tool.Output.GetDoD()

        textplus_tool.SetInput("LayoutType", 1)  # set Type to Text Box

        width = textplus_tool.GetInput("Width")
        height = textplus_tool.GetInput("Height")
        textbox_width = width * textplus_tool.GetInput("LayoutWidth")
        textbox_height = height * textplus_tool.GetInput("LayoutHeight")
        dod_width = dod[3] - dod[1]
        dod_height = dod[4] - dod[2]

        if dod_height != 0:
            size = textbox_height / dod_height
            size *= textplus_tool.GetInput("Size")
            textplus_tool.SetInput("Size", size)

            if dod_width != 0 and textbox_height != 0:
                dod_ratio = dod_width / dod_height
                textbox_ratio = textbox_width / textbox_height

                line_size_x = textbox_ratio / dod_ratio
                line_size_x *= textplus_tool.GetInput("LineSizeX")
                line_size_x = min(1, line_size_x)
                textplus_tool.SetInput("LineSizeX", line_size_x)

    @classmethod
    def _get_subtitle_infos_from_subtitle_track(cls, timeline: Timeline, track_index) -> list[SubtitleInfo]:
        track_handle = TrackHandle("subtitle", track_index)

        if not timeline.has_track(track_handle):
            raise UserError(f"Invalid subtitle track (index={track_index})")

        subtitle_infos = []

        for item in timeline.iter_items_in_track(track_handle):
            subtitle_infos.append(
                SubtitleInfo(
                    content=item._item.GetName(),
                    frame_range=item.get_frame_range(),
                )
            )

        return subtitle_infos

    @classmethod
    def _get_subtitle_infos_from_srt(cls, timeline: Timeline, srt_file_path: str) -> list[SubtitleInfo]:
        path = Path(srt_file_path)

        if not path.is_file():
            raise UserError(f"Invalid file path: '{srt_file_path}'")

        file_content = path.read_text(encoding="utf-8")

        try:
            subtitles = list(srt.parse(file_content))
        except Exception as e:
            raise UserError(f"Failed to parse srt file `{srt_file_path}`. See console for details.", detailed_error=e)

        subtitle_infos = []

        for subtitle in subtitles:
            subtitle_infos.append(
                SubtitleInfo(
                    content=subtitle.content,
                    frame_range=FrameRange(
                        start=Timecode.from_timedelta(subtitle.start, timeline.get_timecode_settings(), False).get_frame(True),
                        end=Timecode.from_timedelta(subtitle.end, timeline.get_timecode_settings(), False).get_frame(True),
                    ),
                )
            )

        return subtitle_infos

    @classmethod
    def _transform_to_subtitles(cls, timeline: Timeline, timeline_items: Iterable[TimelineItem]):
        subtitles = []

        for item in timeline_items:
            subtitles.append(
                srt.Subtitle(
                    index=None,
                    start=timeline.get_item_start_timecode(item).get_timedelta(False),
                    end=timeline.get_item_end_timecode(item).get_timedelta(False),
                    content=item.get_last_fusion_composition().Template.GetInput("StyledText"),  # TODO: support character level styling
                )
            )

        return subtitles

    @classmethod
    def _is_textplus_clip(cls, item: TimelineItem):
        comp = item.get_last_fusion_composition()
        tool = comp.Template if comp is not None else None

        if tool is None:
            return False

        return tool.GetAttrs("TOOLS_RegID") == "TextPlus"

    @classmethod
    def _copy_style(cls, src_item: TimelineItem, dst_items: Iterable[TimelineItem]):
        src_comp = TextPlusComposition(src_item.get_last_fusion_composition())
        src_settings = src_comp.get_settings("UniTextControl", "TextBox")

        cls._copy_style_from_settings(src_settings, dst_items)

    @classmethod
    def _copy_style_from_settings(cls, src_settings: TextPlusSettings, dst_items: Iterable[TimelineItem]):
        new_settings = src_settings

        for i, dst_item in enumerate(dst_items):
            if i % 5 == 4:
                LoadingWindow.set_message(f"Setting {i + 1}/{len(dst_items)} Text+ content...", dispatch_log=False)

            dst_comp = TextPlusComposition(dst_item.get_last_fusion_composition())
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

            # new_settings_has_uni_control = new_settings.get_tool("UniTextControl") is not None
            # uni_control_tool = dst_comp._composition.UniTextControl

            # if not new_settings_has_uni_control and uni_control_tool is not None:
            #     fit = uni_control_tool.GetInput("FitToTextBox")

            #     if fit:
            #         UniTextPlusControl.enable_fit_to_textbox(uni_control_tool)

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
    def _compute_subtitle_insert_ranges(cls, timeline: Timeline, subtitle_infos: list[SubtitleInfo], snap_mode: SnapMode):
        subtitle_ranges = [subtitle_info.frame_range for subtitle_info in subtitle_infos]

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
