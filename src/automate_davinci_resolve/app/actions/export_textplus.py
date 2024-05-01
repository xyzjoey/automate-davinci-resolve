from typing import Optional, NamedTuple, Union
from enum import Enum

from pydantic import BaseModel, Field, root_validator
import srt

from .action_base import ActionBase
from ..enums import ExtraChoice

from ..inputs.paths import SaveFilePathInput
from ...davinci.enums import ClipColor
from ...davinci import textplus_utils
from ...davinci.enums import ResolveStatus
from ...davinci.resolve_app import ResolveApp
from ...davinci.timeline import Timeline
from ...davinci.timecode import Timecode, TimecodeSettings
from ...utils import log


# limitations:
# - does not support clips in compound clip / fusion clip / nested timeline
# - does not support track color


class Inputs(BaseModel):
    subtitle_file: SaveFilePathInput = Field(title="Subtitle File Save Path")
    replace_mode_color: Optional[Union[ExtraChoice, ClipColor]] = Field(
        ExtraChoice.Any,
        title="Replace Mode Clip Color",
    )
    merge_mode_color: Optional[Union[ExtraChoice, ClipColor]] = Field(
        ClipColor.Beige,
        title="Merge Mode Clip Color",
    )
    ignore_mode_color: Optional[Union[ExtraChoice, ClipColor]] = Field(
        ClipColor.Brown,
        title="Ignore Mode Clip Color",
    )

    @root_validator
    def count_any(cls, values):
        count = 0

        if values["replace_mode_color"] == ExtraChoice.Any:
            count += 1

        if values["merge_mode_color"] == ExtraChoice.Any:
            count += 1

        if values["ignore_mode_color"] == ExtraChoice.Any:
            count += 1

        if count > 1:
            raise ValueError(f"At most 1 mode can be Any, get {count} modes being Any")

        return values


class SubtitleMode(Enum):
    Replace = "Replace"
    Merge = "Merge"
    Ignore = "Ignore"


class SubtitleInfo(NamedTuple):
    text: str
    start_frame: int
    end_frame: int
    mode: SubtitleMode


class SubtitleModeMap:
    def __init__(self, inputs: Inputs):
        self.color_to_mode = {}
        self.default_mode = None

        for field_name, mode in {
            "replace_mode_color": SubtitleMode.Replace,
            "merge_mode_color": SubtitleMode.Merge,
            "ignore_mode_color": SubtitleMode.Ignore,
        }.items():
            value = getattr(inputs, field_name)

            if value is not None:
                if isinstance(value, ClipColor):
                    self.color_to_mode[value.value] = mode
                elif value == ExtraChoice.Any:
                    self.default_mode = mode

    def get_mode(self, clip_color: str) -> Optional[SubtitleMode]:
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

    def sorted_iterate(self):  # -> Generator[SubtitleInfo, None, None]:
        for _, text_clip_infos in sorted(self.frame_to_infos.items()):
            for text_clip_info in text_clip_infos:
                yield text_clip_info

    def get_size(self):
        return len(self.infos)


class Action(ActionBase):
    def __init__(self):
        super().__init__(
            name="export_textplus",
            display_name="Export Text+",
            description="Export Text+ from current timeline to .srt file",
            required_status=ResolveStatus.TimelineOpen,
            input_model=Inputs,
        )

    def start(
        self,
        resolve_app: ResolveApp,
        input_data: Inputs,
    ):
        timeline = resolve_app.get_current_timeline()

        log.info(f"[{self}] Collecting Text+ in current timeline...")
        log.flush()
        text_clip_infos = self.get_text_clip_infos(timeline, SubtitleModeMap(input_data))
        log.info(f"[{self}] Collected {text_clip_infos.get_size()} Text+ in current timeline")

        subtitles = self.get_subtitles(text_clip_infos, timeline.get_timecode_settings())
        log.info(f"[{self}] After applying Replace/Merge/Ignore modes, there are {len(subtitles)} subtitles to export")

        file_content = srt.compose(subtitles)
        input_data.subtitle_file.write_text(file_content, encoding="utf-8")

        log.info(f"[{self}] Successfully saved subtitles at {input_data.subtitle_file}!")

    def get_text_clip_infos(self, timeline: Timeline, mode_map: SubtitleModeMap):
        text_clip_infos = TextClipInfoContainer()

        for track_context in timeline.iter_tracks("video"):
            for item in track_context.timeline_items:
                textplus = textplus_utils.find_textplus(item)

                if textplus is not None:
                    text_clip_info = SubtitleInfo(
                        text=textplus.GetInput("StyledText"),
                        start_frame=item.GetStart(),
                        end_frame=item.GetEnd(),
                        mode=mode_map.get_mode(item.GetClipColor()),
                    )
                    text_clip_infos.add(text_clip_info)

        return text_clip_infos

    def get_subtitles(self, infos: TextClipInfoContainer, timecode_settings: TimecodeSettings):
        processed_infos = []

        for info in infos.sorted_iterate():
            if info.mode == SubtitleMode.Ignore:
                continue

            is_overlapped = processed_infos[-1].end_frame >= info.start_frame if len(processed_infos) > 0 else False

            if not is_overlapped:
                processed_infos.append(info)
            else:
                curr = info
                prev = processed_infos[-1]

                # trim overlapped part
                if prev.start_frame >= curr.start_frame:
                    processed_infos.pop()
                else:
                    processed_infos[-1] = prev._replace(end_frame=curr.start_frame)

                # add current subtitle
                if curr.mode == SubtitleMode.Replace:
                    processed_infos.append(curr)
                elif curr.mode == SubtitleMode.Merge:
                    processed_infos.append(curr._replace(text=f"{prev.text}\n{curr.text}", end_frame=prev.end_frame))
                    if prev.end_frame < curr.end_frame:
                        processed_infos.append(curr._replace(start_frame=prev.end_frame))

        return [
            srt.Subtitle(
                index=None,
                start=Timecode.from_frame(info.start_frame, timecode_settings, True).get_timedelta(False),
                end=Timecode.from_frame(info.end_frame, timecode_settings, True).get_timedelta(False),
                content=info.text,
            )
            for info in processed_infos
        ]
