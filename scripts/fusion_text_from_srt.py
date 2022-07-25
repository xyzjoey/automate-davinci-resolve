import os.path
import pprint
from typing import List, Optional, NamedTuple

from pydantic import BaseSettings, Field
import srt

from davinci_utils.clip_color import ClipColor
from davinci_utils.resolve_context import ResolveContext
from utils.terminal_io import TerminalIO
from utils.file_io import FileIO


class MediaPoolFusionCompositionInput:
    def __init__(self, media_pool_fusion_composition):
        self.media_pool_fusion_composition = media_pool_fusion_composition

    def get(self):
        return self.media_pool_fusion_composition

    @classmethod
    def ask_for_input(cls, prompt):
        while True:
            bin_path = TerminalIO.colored_input(prompt)

            try:
                return cls.validate(bin_path)
            except Exception as e:
                TerminalIO.print_error(str(e))

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        bin_path = v
        media_pool_item = ResolveContext.get().get_media_pool_item(bin_path)
        clip_type = media_pool_item.GetClipProperty("Type")

        if clip_type != "Generator":
            raise Exception(f"Expect clip to be a fusion composition (Type=Generator), got Type={clip_type}")

        print("Clip found:")
        print(f"\tClip Name: {media_pool_item.GetClipProperty('Clip Name')}")
        print(f"\tFile Name: {media_pool_item.GetClipProperty('File Name')}")
        print(f"\tName: {media_pool_item.GetName()}")
        print(f"\tType: {media_pool_item.GetClipProperty('Type')}")

        return cls(media_pool_item)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate


class SubtitlesInput:
    def __init__(self, subtitles):
        self.subtitles: List[srt.Subtitle] = subtitles

    def get(self):
        return self.subtitles

    @classmethod
    def ask_for_input(cls, prompt):
        while True:
            TerminalIO.print_question(prompt)
            file_path = FileIO.ask_file(patterns=[".srt"])

            try:
                return cls.validate(file_path)
            except Exception as e:
                TerminalIO.print_error(str(e))

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
    text_clip_input: MediaPoolFusionCompositionInput = Field(
        env="text_clip_bin_path",
        default_factory=lambda: MediaPoolFusionCompositionInput.ask_for_input("Please enter bin location of fusion composition you want to use for generating subtitle\n"
                                                                              "the fusion composition should include text+ node\n"
                                                                              "E.g. 'subfolder/my_fusion_text' (relative path)\n"
                                                                              "E.g. '/folder/my_fusion_text' (add '/' prefix for absolute path)\n"
                                                                              ": ")
    )
    subtitles_input: Optional[SubtitlesInput] = Field(
        env="subtitle_file_path",
        default_factory=lambda: SubtitlesInput.ask_for_input("Please select a subtitle file from the pop up file dialog")
    )
    gap_filler_clip_color: ClipColor = ClipColor.Chocolate


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

        print(f"Will insert {used_subtitle_count} text clips + {gap_filler_count} gap filler clips = {len(subtitle_insert_infos)} clips")

        if len(unused_subtitles) > 0:
            print(f"{len(unused_subtitles)} subtitles will not be added because of overlapping")
            print(f"Skipped subtitles:")
            pprint.pprint({subtitle.index: subtitle.content for subtitle in unused_subtitles})

        return subtitle_insert_infos

    def prepare_timeline(self):
        timeline_name, timeline = self.resolve_context.create_timeline("Generated Subtitles")

        print(f"Created timeline '{timeline_name}' under current folder '{self.resolve_context.media_pool.GetCurrentFolder().GetName()}'")

        return timeline

    def insert_subtitles(self, timeline, media_pool_text_clip, gap_filler_clip_color, subtitle_insert_infos):
        print(f"Inserting {len(subtitle_insert_infos)} clips into timeline '{timeline.GetName()}'...")

        insert_args = [{
            "mediaPoolItem": media_pool_text_clip,
            "startFrame": 0,
            "endFrame": insert_info.frames - 1,
        } for insert_info in subtitle_insert_infos]

        self.resolve_context.project.SetCurrentTimeline(timeline)
        timeline_items = self.resolve_context.media_pool.AppendToTimeline(insert_args)

        assert timeline_items is not None, "Failed to add text clips"
        assert len(subtitle_insert_infos) == len(timeline_items)

        for i, (insert_info, timeline_item) in enumerate(zip(subtitle_insert_infos, timeline_items)):
            print(f"Setting clip content ({i + 1}/{len(timeline_items)})...", end="\r")

            comp = timeline_item.GetFusionCompByIndex(1)
            text_node = comp.FindToolByID("TextPlus")

            if not insert_info.is_gap_filler:
                text_node.SetInput("StyledText", insert_info.text_content)
            else:
                timeline_item.SetClipColor(gap_filler_clip_color.value)
                text_node.Delete()

                background = comp.Background()
                background.SetInput("TopLeftAlpha", 0)
                media_out = comp.FindToolByID("MediaOut")
                media_out.ConnectInput("Input", background)

        print()
        print("Done")

    def run_with_input(self, inputs: Inputs):
        subtitle_insert_infos = self.prepare_subtitle_insert_infos(inputs.subtitles_input.get())
        timeline = self.prepare_timeline()

        self.insert_subtitles(timeline, inputs.text_clip_input.get(), inputs.gap_filler_clip_color, subtitle_insert_infos)

    def run(self):
        self.resolve_context.update()
        inputs = Inputs()

        if inputs.subtitles_input is None:
            TerminalIO.print_warning("Cancelled")
            return

        self.run_with_input(inputs)

    def main(self):
        self.run()


if __name__ == "__main__":
    Process().main()
