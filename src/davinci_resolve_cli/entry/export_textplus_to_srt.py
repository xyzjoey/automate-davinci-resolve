from enum import Enum
from typing import Any, Generator, NamedTuple

from pydantic import BaseSettings, Field
import srt

from davinci_resolve_cli.davinci import textplus_utils
from davinci_resolve_cli.davinci.clip_color import ClipColor
from davinci_resolve_cli.action.action_base import ActionBase, ActionResult
from davinci_resolve_cli.inputs.file_path_input import SaveFilePath
from davinci_resolve_cli.utils import terminal_io


# limitations:
# - does not support clips in compound clip / fusion clip / nested timeline
# - does not support track color


class SubtitleMode(Enum):
    Replace = "Replace"
    Merge = "Merge"
    Ignore = "Ignore"


class SubtitleInfo(NamedTuple):
    text: str
    start_frame: int
    end_frame: int
    item: Any
    mode: SubtitleMode


class Inputs(BaseSettings):
    subtitle_path: SaveFilePath = Field(
        description="Path to export subtitle file",
        default_factory=lambda: SaveFilePath.ask_for_input("subtitle export", patterns=[".srt"])
    )
    default_mode: SubtitleMode = Field(
        SubtitleMode.Replace,
        description="Default method of converting a Text+ clip to subtitle. Replace: trim previous overlapping clip. Merge: merge with previous overlapping clip. Ignore: ignore the current clip.",
        env="default_subtitle_mode",
    )
    replace_mode_color: ClipColor = Field(
        None,
        description="Clip color for replace mode.",
        env="subtitle_replace_mode_color",
    )
    merge_mode_color: ClipColor = Field(
        None,
        description="Clip color for merge mode.",
        env="subtitle_merge_mode_color",
    )
    ignore_mode_color: ClipColor = Field(
        None,
        description="Clip color for ignore mode.",
        env="subtitle_ignore_mode_color",
    )


class SubtitleModeMap:
    def __init__(self, inputs: Inputs):
        self.color_to_mode = {}
        self.default_mode = inputs.default_mode

        if inputs.replace_mode_color is not None:
            self.color_to_mode[inputs.replace_mode_color.value] = SubtitleMode.Replace
        if inputs.merge_mode_color is not None:
            self.color_to_mode[inputs.merge_mode_color.value] = SubtitleMode.Merge
        if inputs.ignore_mode_color is not None:
            self.color_to_mode[inputs.ignore_mode_color.value] = SubtitleMode.Ignore

    def get_mode(self, clip_color: str):
        return self.color_to_mode.get(clip_color, self.default_mode)


class TextClipInfoContainer:
    def __init__(self):
        self.infos = []
        self.frame_to_infos = {}

    def add(self, text_clip_info):
        frame = text_clip_info.start_frame
        self.frame_to_infos.setdefault(frame, [])
        self.frame_to_infos[frame].append(text_clip_info)
        self.infos.append(text_clip_info)

    def sorted_iterate(self) -> Generator[SubtitleInfo, None, None]:
        for frame, text_clip_infos in sorted(self.frame_to_infos.items()):
            for text_clip_info in text_clip_infos:
                yield text_clip_info

    def get_size(self):
        return len(self.infos)


class Action(ActionBase):
    def __init__(self):
        super().__init__(input_model=Inputs)

    def get_text_clip_infos(self, timeline_context, mode_map: SubtitleModeMap):
        text_clip_infos = TextClipInfoContainer()
        timeline_context = self.resolve_context.get_current_timeline_context()

        for track_context in timeline_context.iterate_tracks("video"):
            for item in track_context.timeline_items:
                textplus = textplus_utils.find_textplus(item)

                if textplus is not None:
                    text_clip_info = SubtitleInfo(
                        text=textplus.GetInput("StyledText"),
                        start_frame=item.GetStart(),
                        end_frame=item.GetEnd(),
                        item=item,
                        mode=mode_map.get_mode(item.GetClipColor()),
                    )
                    text_clip_infos.add(text_clip_info)

        return text_clip_infos

    def get_subtitles(self, infos: TextClipInfoContainer, timecode_context):
        processed_infos = []
        subtitles = []

        for info in infos.sorted_iterate():
            if info.mode == SubtitleMode.Ignore:
                continue
            
            is_overlapped = processed_infos[-1].end_frame >= info.start_frame if len(processed_infos) > 0 else False

            if not is_overlapped:
                processed_infos.append(info)
            else:
                curr = info
                prev = processed_infos[-1]

                if prev.start_frame >= curr.start_frame:
                    processed_infos.pop()
                else:
                    processed_infos[-1] = prev._replace(end_frame=curr.start_frame)

                if curr.mode == SubtitleMode.Replace:
                    processed_infos.append(curr)
                elif curr.mode == SubtitleMode.Merge:
                    processed_infos.append(curr._replace(text=f"{prev.text}\n{curr.text}", end_frame=prev.end_frame))
                    if prev.end_frame < curr.end_frame:
                        processed_infos.append(curr._replace(start_frame=prev.end_frame))

        for info in processed_infos:
            subtitles.append(srt.Subtitle(
                index=None,
                start=timecode_context.create_timecode_from_frame(info.start_frame, start_timecode_is_applied=True).get_timedelta(),
                end=timecode_context.create_timecode_from_frame(info.end_frame, start_timecode_is_applied=True).get_timedelta(),
                content=info.text,
            ))

        return subtitles

    async def run_with_input(self, inputs: Inputs):
        timeline_context = self.resolve_context.get_current_timeline_context()
        
        terminal_io.print_info(f"Finding Text+ in current timeline...")
        text_clip_infos = self.get_text_clip_infos(timeline_context, SubtitleModeMap(inputs))
        terminal_io.print_info(f"Found {text_clip_infos.get_size()} Text+ in current timeline")
        
        terminal_io.print_info(f"Convert Text+ to subtitles...")
        subtitles = self.get_subtitles(text_clip_infos, timeline_context.get_timecode_context())
        
        terminal_io.print_info(f"{len(subtitles)} subtitles to export")
        file_content = srt.compose(subtitles)
        inputs.subtitle_path.get().write_text(file_content, encoding="utf-8")
        terminal_io.print_info(f"Successfully saved subtitles at {inputs.subtitle_path.get()}!")

        return ActionResult.Done


if __name__ == "__main__":
    Action().main()

