import copy
import itertools
from pathlib import Path
from pprint import pprint
from typing import Iterable, NamedTuple

import srt

from ..extended_resolve import davinci_resolve_module
from ..extended_resolve.media_pool_item import MediaPoolItem
from ..extended_resolve.resolve import MediaPoolItemInsertInfo
from ..extended_resolve.textplus import TextPlusComposition
from ..extended_resolve.timecode import Timecode
from ..extended_resolve.timeline import Timeline
from ..extended_resolve.timeline_item import TimelineItem
from ..extended_resolve.track import TrackHandle
from ..resolve_types import PyRemoteComposition, PyRemoteOperator
from ..utils.math import FrameRange
from .constants import CharacterLevelStylingCopyMode, GeneratedTrackName, SnapMode
from .errors import UserError
from .smart_edit_bin import SmartEditBin
from .textplus_custom_data import TextPlusCustomData
from .ui.loading_window import LoadingWindow

LineRange = tuple[int, int]

INPUT_IDS_FOR_DOD_SIMULATE = {
    # text page
    "StyledText",
    "Font",
    "Style",
    "Size",
    "VerticalTopCenterBottom",
    "VerticallyJustified",
    "HorizontalLeftCenterRight",
    "HorizontallyJustified",
    "Direction",
    "LineDirection",
    # text page tab
    "Tab1Position",
    "Tab1Alignment",
    "Tab2Position",
    "Tab2Alignment",
    "Tab3Position",
    "Tab3Alignment",
    "Tab4Position",
    "Tab4Alignment",
    "Tab5Position",
    "Tab5Alignment",
    "Tab6Position",
    "Tab6Alignment",
    "Tab7Position",
    "Tab7Alignment",
    "Tab8Position",
    "Tab8Alignment",
    # text page advanced controls
    "ReadingDirection",
    "ForceMonospaced",
    "UseFontKerning",
    "UseLigatures",
    "SplitLigatures",
    "StylisticSet",
    "FontFeatures",
    # layout page
    "LayoutType",
    "Wrap",
    # "CenterZ",
    "LayoutWidth",
    "LayoutHeight",
    # "Perspective",
    # transform page
    "LineSpacing",
    "WordSpacing",
    "CharacterSpacing",
    "LineSizeX",
    "LineSizeY",
    "WordSizeX",
    "WordSizeY",
    "CharacterSizeX",
    "CharacterSizeY",
}


class TextplusLinkTool:
    def __init__(self, _tool: PyRemoteOperator):
        self._tool = _tool

    @classmethod
    def get_from_connected_textplus_tool(cls, textplus_tool: PyRemoteOperator) -> "TextplusLinkTool":
        for connected_input in textplus_tool.Output.GetConnectedInputs().values():
            connected_tool = connected_input.GetTool()

            if connected_tool is not None and connected_tool.ID == "Fuse.TextPlusLink":
                return TextplusLinkTool(connected_tool)

        return None

    @classmethod
    def get_from_or_create_and_connect_textplus_tool(cls, textplus_tool: PyRemoteOperator) -> "TextplusLinkTool":
        link_tool = cls.get_from_connected_textplus_tool(textplus_tool)

        if link_tool is None:
            comp = textplus_tool.Composition

            _tool = comp.AddTool("Fuse.TextPlusLink")
            _tool.TextPlus.ConnectTo(textplus_tool.Output)
            link_tool = TextplusLinkTool(_tool)

        return link_tool

    def get_connected_dod_simulate_tool(self) -> PyRemoteOperator | None:
        out = self._tool.TextDodSimulate.GetConnectedOutput()

        return out.GetTool() if out is not None else None

    def get_or_create_connected_dod_simulate_tool(self, name: str = "TextDodSimulate") -> PyRemoteOperator:
        dod_simulate_tool = self.get_connected_dod_simulate_tool()

        if dod_simulate_tool is None:
            comp = self._tool.Composition

            dod_simulate_tool = comp.AddTool("TextPlus")
            dod_simulate_tool.SetAttrs({"TOOLS_Name": name})

            self._tool.TextDodSimulate.ConnectTo(dod_simulate_tool.Output)

        return dod_simulate_tool

    def init_expressions(self):
        if self._tool.TextBoxCenter.GetExpression() is None:
            self._tool.TextBoxCenter.SetExpression("self:GetSourceTool('TextPlus').Center")

        if self._tool.TextBoxWidth.GetExpression() is None:
            self._tool.TextBoxWidth.SetExpression("self:GetSourceTool('TextPlus').LayoutWidth")

        if self._tool.TextBoxHeight.GetExpression() is None:
            self._tool.TextBoxHeight.SetExpression("self:GetSourceTool('TextPlus').LayoutHeight")

        dod_name = "self:GetSourceTool('TextDodSimulate').Output.DataWindow"  # not able to fetch by using dod_simulate_tool.Name (unknown reason)

        if self._tool.DodSimulateWidth.GetExpression() is None:
            self._tool.DodSimulateWidth.SetExpression(f"{dod_name}[3] - {dod_name}[1]")

        if self._tool.DodSimulateHeight.GetExpression() is None:
            self._tool.DodSimulateHeight.SetExpression(f"{dod_name}[4] - {dod_name}[2]")

    @classmethod
    def enable_fit_to_textbox(cls, textplus_tool: PyRemoteOperator):
        link_tool = TextplusLinkTool.get_from_or_create_and_connect_textplus_tool(textplus_tool)
        link_tool.init_expressions()

        dod_simulate_tool = link_tool.get_or_create_connected_dod_simulate_tool(
            name="TextDodSimulate1"
        )  # don't name `TextDodSimulate` to avoid wrong auto rename in expression

        TEXTPLUS_EXPRESSION_TARGETS = {"LayoutSize", "LineSizeX"}

        for input_id in INPUT_IDS_FOR_DOD_SIMULATE:
            input = getattr(dod_simulate_tool, input_id)

            if input_id in TEXTPLUS_EXPRESSION_TARGETS:
                if input.GetExpression() is not None:
                    input.SetExpression()  # avoid circular dependency
                dod_simulate_tool.SetInput(input_id, 1.0)  # normalize to simplify expression
            else:
                if input.GetExpression() is None:
                    input.SetExpression(f"{textplus_tool.Name}.{input_id}")

        dod_width = f"{link_tool._tool.Name}.DodSimulateWidth"
        dod_height = f"{link_tool._tool.Name}.DodSimulateHeight"

        textbox_width = f"(Width * {link_tool._tool.Name}.TextBoxWidth)"
        textbox_height = f"(Height * {link_tool._tool.Name}.TextBoxHeight)"

        textplus_tool.SetInput("LayoutType", 1)  # set LayoutType to Text Box
        textplus_tool.SetInput("Wrap", False)  # wrap is not supported together with fit to textbox
        textplus_tool.LayoutSize.SetExpression(f"iif({dod_height} ~= 0, {textbox_height} / {dod_height}, 1.0)")
        textplus_tool.LineSizeX.SetExpression(f"iif({dod_width} ~= 0, min(1.0, {textbox_width} * {dod_height} / ({dod_width} * {textbox_height})), 1.0)")

    @classmethod
    def disable_fit_to_textbox(cls, textplus_tool: PyRemoteOperator):
        if textplus_tool.LayoutSize.GetExpression() is not None:
            textplus_tool.LayoutSize.SetExpression()

        if textplus_tool.LineSizeX.GetExpression() is not None:
            textplus_tool.LineSizeX.SetExpression()

        link_tool = TextplusLinkTool.get_from_connected_textplus_tool(textplus_tool)

        if link_tool is None:
            return

        dod_simulate_tool = link_tool.get_connected_dod_simulate_tool()

        link_tool._tool.Delete()

        if dod_simulate_tool is not None:
            dod_simulate_tool.Delete()


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
        src_settings = src_comp.get_settings()
        char_level_style_copy_mode = TextPlusCustomData.get_character_styling_level_copy_mode(src_comp._composition)

        for i, dst_item in enumerate(dst_items):
            if i % 5 == 4:
                LoadingWindow.set_message(f"Setting {i + 1}/{len(dst_items)} Text+ content...", dispatch_log=False)

            dst_comp = TextPlusComposition(dst_item.get_last_fusion_composition())
            old_settings = dst_comp.get_settings(tools=[dst_comp._composition.Template])
            text_value = old_settings.get_text_value()

            new_settings = copy.deepcopy(src_settings)
            new_settings.set_text_value(text_value)

            if char_level_style_copy_mode == CharacterLevelStylingCopyMode.MAP_TO_LINES:
                char_level_style_settings = new_settings.find_character_level_styling()

                if char_level_style_settings is not None:
                    old_style_array = char_level_style_settings.get_style_array()
                    new_style_array = cls._map_style_array_to_lines(old_style_array, text_value)
                    char_level_style_settings.set_style_array(new_style_array)

            dst_comp.set_settings(new_settings)

    @classmethod
    def _map_style_array_to_lines(cls, style_array: dict, text: str):
        # example
        # CharacterLevelStyling = Input {
        # 	Value = StyledText {
        # 		Array = {
        # 			{ 102, 7, 11, Value = 0.033 },
        # 			{ 2401, 10, 11, Value = 0.156862750649452 },
        # 			{ 2402, 10, 11, Value = 0.0823529437184334 },
        # 			{ 2403, 10, 11, Value = 1 },
        # 			{ 2401, 12, 12, Value = 0.156862795352936 },
        # 			{ 2402, 12, 12, Value = 0.0823529437184334 },
        # 			{ 2403, 12, 12, Value = 1 },
        # 			{ 102, 12, 12, Value = 0.181 }
        # 		}
        # 	},
        # }

        style_grouped_by_line: dict[LineRange, list[dict] | None] = {}
        old_line_ranges = []
        new_line_ranges = []

        # group by line
        for style_item in style_array.values():
            line_range = (style_item[2], style_item[3])
            style_grouped_by_line.setdefault(line_range, [])
            style_grouped_by_line[line_range].append(style_item)

        last_line_end = 0

        # build old_line_ranges
        for line_range in sorted(style_grouped_by_line.keys()):
            if line_range[0] > last_line_end:
                old_line_ranges.append((last_line_end, line_range[0] - 1))
            old_line_ranges.append(line_range)
            last_line_end = line_range[1]

        new_line_ranges = cls._get_line_ranges(text)

        # merge exceeding line ranges
        if len(old_line_ranges) < len(new_line_ranges):
            last_line_range = (
                new_line_ranges[len(old_line_ranges) - 1][0],
                new_line_ranges[-1][1],
            )
            new_line_ranges[len(old_line_ranges) - 1] = last_line_range
            new_line_ranges = new_line_ranges[: len(old_line_ranges)]

        new_style_array = {}

        for old_line_range, new_line_range in zip(old_line_ranges, new_line_ranges):
            style_items = style_grouped_by_line.get(old_line_range)

            if style_items is not None:
                for style_item in style_items:
                    style_item[2] = new_line_range[0]
                    style_item[3] = new_line_range[1]
                    new_style_array[len(new_style_array) + 1] = style_item

        return new_style_array

    @classmethod
    def _get_line_ranges(cls, text: str) -> list[LineRange]:
        ranges = []
        next_start = 0

        for i, line in enumerate(text.splitlines()):
            end = next_start + len(line)
            ranges.append((next_start, end))
            next_start = end + 1

        return ranges

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
