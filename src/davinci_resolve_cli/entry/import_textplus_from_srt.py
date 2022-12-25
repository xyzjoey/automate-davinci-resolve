from contextlib import contextmanager
import os
import pprint
import tempfile
from typing import List, Optional, NamedTuple

from pydantic import BaseSettings, Field
import srt

from davinci_resolve_cli.action.action_base import ActionBase, ActionResult
from davinci_resolve_cli.davinci import textplus_utils
from davinci_resolve_cli.davinci.clip_color import ClipColor
from davinci_resolve_cli.davinci.timecode import Timecode, TimecodeContext
from davinci_resolve_cli.davinci.resolve_context import ResolveStatus
from davinci_resolve_cli.utils import terminal_io
from davinci_resolve_cli.inputs.file_path_input import LoadFilePathInput


class SubtitleFileInput(LoadFilePathInput):
    @classmethod
    def parse(cls, v: "SubtitleFileInput"):
        if v.parsed_data is not None:
            return v

        try:
            terminal_io.print_info(f"Parsing subtitles from '{v.get()}'...")

            with open(v.get(), encoding="utf-8") as f:
                subtitles = list(srt.parse("".join(f.readlines())))

                terminal_io.print_info(f"Parsed {len(subtitles)} subtitles")

                v.parsed_data = subtitles
                return v

        except Exception as e:
            raise ValueError(f"Failed to parse subtitle file:\n{e}")

    @classmethod
    def ask_input(cls):
        return super().ask_input("subtitle file", [".srt"])


class Inputs(BaseSettings):
    subtitle_file_input: SubtitleFileInput = Field(
        alias="subtitle_path",
        env="subtitle_import_path",
        default_factory=lambda: SubtitleFileInput.ask_input()
    )
    gap_filler_clip_color: Optional[ClipColor] = None


class SubtitleInsertInfo(NamedTuple):
    text_content: Optional[str]
    frames: int


class SubtitleInsertContext(NamedTuple):
    frame_rate: float
    infos: List[SubtitleInsertInfo]


class Action(ActionBase):
    def __init__(self):
        super().__init__(
            input_model=Inputs,
            required_resolve_status=ResolveStatus.ProjectAvail
        )

    @contextmanager
    def temp_project(self, project_file_path, project_name_format):
        current_project_name = self.resolve_context.project.GetName()
        temp_project_name = project_name_format.format(next(tempfile._get_candidate_names()))

        terminal_io.print_info(f"Importing temporary project '{temp_project_name}'...")
        assert self.resolve_context.project_manager.ImportProject(project_file_path, temp_project_name), f"Failed to import project '{temp_project_name}' from {project_file_path} (does same project name exist?)"
        assert self.resolve_context.project_manager.LoadProject(temp_project_name) is not None

        self.resolve_context.update()

        yield

        terminal_io.print_info(f"Loading back previous project '{current_project_name}'...")
        assert self.resolve_context.project_manager.LoadProject(current_project_name) is not None
        assert self.resolve_context.project_manager.DeleteProject(temp_project_name)
        terminal_io.print_info(f"Removed temporary project")

        self.resolve_context.update()

    def prepare_subtitle_insert_context(self, subtitles):
        timecode_context = TimecodeContext("01:00:00:00", self.resolve_context.project.GetSetting("timelineFrameRate"))

        subtitle_insert_context = SubtitleInsertContext(frame_rate=timecode_context.frame_rate, infos=[])
        skipped_subtitles = []

        last_frame = 0

        for subtitle in subtitles:
            subtitle_start_frame = Timecode.from_timedelta(subtitle.start, timecode_context, False).get_frame(False)
            subtitle_end_frame = Timecode.from_timedelta(subtitle.end, timecode_context, False).get_frame(False)

            if last_frame > subtitle_start_frame:  # there is overlap
                skipped_subtitles.append(subtitle)
                continue

            if last_frame < subtitle_start_frame:  # there is gap
                subtitle_insert_context.infos.append(SubtitleInsertInfo(
                    text_content=None,
                    frames=(subtitle_start_frame - last_frame),
                ))

            subtitle_insert_context.infos.append(SubtitleInsertInfo(
                text_content=subtitle.content,
                frames=(subtitle_end_frame - subtitle_start_frame),
            ))

            last_frame = subtitle_end_frame

        clip_count = len(subtitle_insert_context.infos)
        subtitle_clip_count = sum(1 for info in subtitle_insert_context.infos if info.text_content is not None)
        gap_filler_count = clip_count - subtitle_clip_count

        terminal_io.print_info(f"Will insert ({subtitle_clip_count} Text+) + ({gap_filler_count} gap filler) = {clip_count} clips")

        if len(skipped_subtitles) > 0:
            terminal_io.print_info(f"{len(skipped_subtitles)} subtitles will be skipped because of overlapping")
            terminal_io.print_info(f"Skipped subtitles:")
            pprint.pprint({subtitle.index: subtitle.content for subtitle in skipped_subtitles})

        return subtitle_insert_context

    def create_subtitle_timeline(self, inputs: Inputs, subtitle_insert_context: SubtitleInsertContext):
        clip_count = len(subtitle_insert_context.infos)

        media_pool_context = self.resolve_context.get_media_pool_context()
        media_pool_textplus = media_pool_context.find_item(lambda item: item.GetClipProperty("Clip Name") == "Text+" and item.GetClipProperty("Type") == "Generator")
        media_pool_dummy = media_pool_context.find_item(lambda item: item.GetClipProperty("Clip Name") == "GapFiller" and item.GetClipProperty("Type") == "Generator")
        # media_pool_dummy.SetClipColor(inputs.gap_filler_clip_color.value)  # no effect

        terminal_io.print_info(f"Creating subtitle timeline with {clip_count} clips...")

        timeline = self.resolve_context.media_pool.CreateEmptyTimeline("AutoSubtitle")

        assert timeline is not None, f"Failed to create timeline 'AutoSubtitle'"

        # below has no effect, use project frame rate ("timelineFrameRate" is read-only?)
        # timeline.SetSetting("timelineFrameRate", str(subtitle_insert_context.frame_rate))

        timeline_items = self.resolve_context.media_pool.AppendToTimeline([{
            "mediaPoolItem": media_pool_textplus if insert_info.text_content is not None else media_pool_dummy,
            "startFrame": 0,
            "endFrame": insert_info.frames - 1,
        } for insert_info in subtitle_insert_context.infos])

        # below does not work. CreateTimelineFromClips cannot add same clip twice?
        # timeline = self.resolve_context.media_pool.CreateTimelineFromClips("AutoSubtitle", clip_infos)

        assert clip_count == len(timeline_items), f"Expect {clip_count} clips in timeline, get {len(timeline_items)}"

        for i, (insert_info, timeline_item) in enumerate(zip(subtitle_insert_context.infos, timeline_items)):
            terminal_io.print_info(f"Setting clip content ({i + 1}/{len(timeline_items)})...", end="\r")

            if insert_info.text_content is not None:
                textplus = textplus_utils.find_textplus(timeline_item)
                textplus.SetInput("StyledText", insert_info.text_content)
            elif inputs.gap_filler_clip_color is not None:
                timeline_item.SetClipColor(inputs.gap_filler_clip_color.value)

        terminal_io.print_info("")

        return timeline

    def run_with_input(self, inputs: Inputs):
        temp_timeline_path = f"{self.settings.temp_dir}/auto_subtitles.drt"
        temp_project_path = f"{self.settings.data_dir}/auto_subtitle.drp"

        with self.temp_project(temp_project_path, "auto_subtitle_{}"):
            subtitle_insert_context = self.prepare_subtitle_insert_context(inputs.subtitle_file_input.get_parsed())
            timeline = self.create_subtitle_timeline(inputs, subtitle_insert_context)

            assert timeline.Export(temp_timeline_path, self.resolve_context.resolve.EXPORT_DRT, self.resolve_context.resolve.EXPORT_NONE)

        timeline = self.resolve_context.media_pool.ImportTimelineFromFile(temp_timeline_path)

        assert timeline is not None, f"Failed to import timeline from {temp_timeline_path}"

        terminal_io.print_info(f"Successfully created subtitle timeline '{timeline.GetName()}'!")

        os.remove(temp_timeline_path)

        return ActionResult.Done


if __name__ == "__main__":
    Action().main()
