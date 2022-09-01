import os.path
import pprint
from typing import List, Optional, NamedTuple

from pydantic import BaseSettings, Field
import srt

from davinci_resolve_cli.utils import terminal_io
from davinci_resolve_cli.davinci.clip_color import ClipColor
from davinci_resolve_cli.davinci.resolve_context import ResolveContext, ResolveStatus
from davinci_resolve_cli.utils.file_io import FileIO


class MediaPoolTextPlusInput:
    def __init__(self, media_pool_fusion_composition):
        self.media_pool_fusion_composition = media_pool_fusion_composition

    def get(self):
        return self.media_pool_fusion_composition

    @classmethod
    def ask_for_input(cls):
        resolve_context = ResolveContext.get()

        while True:
            for media_pool_item, folders in resolve_context.iter_media_pool_items():
                if (media_pool_item.GetClipProperty("Clip Name") == "Text+" and media_pool_item.GetClipProperty("Type") == "Generator"):
                    print(f"Text+ found in Media Pool at {'/'.join([folder.GetName() for folder in folders])}")

                    return cls(media_pool_item)

            terminal_io.print_error("Text+ not found in Media Pool\n"
                                   "Due to scripting API limitation, it is required for user to put Text+ in Media Pool in advance")
            terminal_io.colored_input("Please put Text+ in anywhere in Media Pool and press Enter: ")

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        raise Exception(f"Expected {cls}, get {type(v)}")

    @classmethod
    def __get_validators__(cls):
        yield cls.validate


class SubtitlesInput:
    def __init__(self, subtitles):
        self.subtitles: List[srt.Subtitle] = subtitles

    def get(self):
        return self.subtitles

    @classmethod
    def ask_for_input(cls):
        while True:
            terminal_io.print_question("Please select a subtitle file from the pop up file dialog")
            file_path = FileIO.ask_file(patterns=[".srt"])

            try:
                return cls.validate(file_path)
            except Exception as e:
                terminal_io.print_error(str(e))

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        file_path = v

        if file_path == "":
            return None

        if not os.path.exists(file_path):
            raise Exception(f"{file_path} does not exist")

        try:
            print(f"Parsing subtitles from '{file_path}'...")

            with open(file_path, encoding="utf-8") as f:
                subtitles = list(srt.parse("".join(f.readlines())))

                print(f"Parsed {len(subtitles)} subtitles")

                return cls(subtitles)

        except Exception as e:
            raise Exception(f"Failed to parse subtitle file:\n{e}")

    @classmethod
    def __get_validators__(cls):
        yield cls.validate


class SubtitleInsertInfo(NamedTuple):
    text_content: str
    frames: int
    is_gap_filler: bool


class Inputs(BaseSettings):
    media_pool_textplus_input: MediaPoolTextPlusInput = Field(default_factory=lambda: MediaPoolTextPlusInput.ask_for_input())
    subtitles_input: Optional[SubtitlesInput] = Field(env="subtitle_file_path", default_factory=lambda: SubtitlesInput.ask_for_input())
    gap_filler_clip_color: ClipColor


class Process:
    def __init__(self):
        self.resolve_context = ResolveContext.get()

    def prepare_subtitle_insert_infos(self, subtitles):
        subtitle_insert_infos = []
        unused_subtitles = []
        used_subtitle_count = 0
        gap_filler_count = 0

        last_frame = 0

        for subtitle in subtitles:
            subtitle_start_frame = self.resolve_context.timedelta_to_frame(subtitle.start)
            subtitle_end_frame = self.resolve_context.timedelta_to_frame(subtitle.end)

            if last_frame > subtitle_start_frame:
                unused_subtitles.append(subtitle)
                continue

            if last_frame < subtitle_start_frame:
                subtitle_insert_infos.append(SubtitleInsertInfo(
                    text_content="",
                    frames=(subtitle_start_frame - last_frame),
                    is_gap_filler=True,
                ))
                gap_filler_count += 1

            subtitle_insert_infos.append(SubtitleInsertInfo(
                text_content=subtitle.content,
                frames=(subtitle_end_frame - subtitle_start_frame),
                is_gap_filler=False,
            ))

            used_subtitle_count += 1
            last_frame = subtitle_end_frame

        print(f"Will insert ({used_subtitle_count} Text+) + ({gap_filler_count} gap filler) = {len(subtitle_insert_infos)} clips")

        if len(unused_subtitles) > 0:
            print(f"{len(unused_subtitles)} subtitles will not be added because of overlapping")
            print(f"Skipped subtitles:")
            pprint.pprint({subtitle.index: subtitle.content for subtitle in unused_subtitles})

        return subtitle_insert_infos

    def prepare_timeline(self):
        timeline_name, timeline = self.resolve_context.create_timeline("Generated Subtitles")

        print(f"Created timeline '{timeline_name}' under current folder '{self.resolve_context.media_pool.GetCurrentFolder().GetName()}'")

        return timeline

    def insert_subtitles(self, timeline, media_pool_textplus, gap_filler_clip_color, subtitle_insert_infos):
        print(f"Inserting {len(subtitle_insert_infos)} clips into timeline '{timeline.GetName()}'...")

        insert_args = [{
            "mediaPoolItem": media_pool_textplus,
            "startFrame": 0,
            "endFrame": insert_info.frames - 1,
        } for insert_info in subtitle_insert_infos]

        self.resolve_context.project.SetCurrentTimeline(timeline)
        timeline_items = self.resolve_context.media_pool.AppendToTimeline(insert_args)

        assert timeline_items is not None, "Failed to add clips"
        assert len(subtitle_insert_infos) == len(timeline_items)

        for i, (insert_info, timeline_item) in enumerate(zip(subtitle_insert_infos, timeline_items)):
            print(f"Setting clip content ({i + 1}/{len(timeline_items)})...", end="\r")

            comp = timeline_item.GetFusionCompByIndex(1)
            textplus = comp.FindToolByID("TextPlus")

            if not insert_info.is_gap_filler:
                textplus.SetInput("StyledText", insert_info.text_content)
            else:
                timeline_item.SetClipColor(gap_filler_clip_color.value)
                textplus.Delete()

                background = comp.Background()
                background.SetInput("TopLeftAlpha", 0)
                media_out = comp.FindToolByID("MediaOut")
                media_out.ConnectInput("Input", background)

        print()
        print("Done")

    def run_with_input(self, inputs: Inputs):
        subtitle_insert_infos = self.prepare_subtitle_insert_infos(inputs.subtitles_input.get())
        timeline = self.prepare_timeline()

        self.insert_subtitles(timeline, inputs.media_pool_textplus_input.get(), inputs.gap_filler_clip_color, subtitle_insert_infos)

    def run(self):
        status = self.resolve_context.update()

        if status == ResolveStatus.NotAvail:
            terminal_io.print_error("Failed to load Davinci Resolve script app. Is Davinci Resolve running?")
        elif status == ResolveStatus.ProjectAvail:
            terminal_io.print_error("Davinci Resolve project is not opened")
        else:
            inputs = Inputs()

            if inputs.subtitles_input is None:
                terminal_io.print_warning("Cancelled")
                return

            self.run_with_input(inputs)

    def main(self):
        self.run()


if __name__ == "__main__":
    Process().main()
