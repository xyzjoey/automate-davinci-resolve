from datetime import datetime
import os
from typing import Optional, NamedTuple

from pydantic import BaseModel, Field
import srt

from .action_base import ActionBase
from ..inputs.subtitles import SubtitleFileInput
from ..settings import AppSettings
from ...davinci import textplus_utils
from ...davinci.enums import ResolveStatus
from ...davinci.resolve_app import ResolveApp
from ...davinci.timecode import Timecode, TimecodeSettings
from ...utils import log


class Inputs(BaseModel):
    subtitle_file: SubtitleFileInput = Field(title="Subtitle File")


class SubtitleInfo(NamedTuple):
    text_content: Optional[str]
    record_frame: int
    frames: int


class Action(ActionBase):
    timecode_settings = TimecodeSettings("01:00:00:00", 60.0)

    def __init__(self):
        super().__init__(
            name="import_textplus",
            display_name="Import Text+",
            description="Import Text+ from .srt file to a new timeline",
            required_status=ResolveStatus.ProjectOpen,
            input_model=Inputs,
        )

    def start(
        self,
        app_settings: AppSettings,
        resolve_app: ResolveApp,
        input_data: Inputs,
    ):
        with log.prefix(f"[{self}]"):
            datetime_formatted = datetime.now().strftime("%Y%m%d%H%M%S")
            subtitle_project_path = f"{app_settings.data_dir}/auto_subtitle.drp"
            temp_timeline_path = f"{app_settings.temp_dir}/auto_subtitles_{datetime_formatted}.drt"

            with resolve_app.import_temp_project(
                subtitle_project_path,
                project_name=f"auto_subtitle_{datetime_formatted}",
            ) as project:
                if project is None:
                    return

                subtitle_infos = self.prepare_subtitle_infos(input_data.subtitle_file.parsed)
                timeline = self.create_subtitle_timeline(resolve_app, subtitle_infos)

                if timeline is None:
                    return

                result = timeline.Export(temp_timeline_path, resolve_app.resolve.EXPORT_DRT, resolve_app.resolve.EXPORT_NONE)

                if not result:
                    log.error(f"Failed to export timeline to {temp_timeline_path}")
                    return

            timeline = resolve_app.media_pool.ImportTimelineFromFile(temp_timeline_path)

            if timeline is None:
                log.error(f"Failed to import timeline from {temp_timeline_path}")
                return

            log.info(f"Successfully created subtitle timeline '{timeline.GetName()}'!")

            os.remove(temp_timeline_path)

    def prepare_subtitle_infos(self, subtitles: list[srt.Subtitle]):
        subtitle_infos: list[SubtitleInfo] = []
        skipped_subtitles = []

        last_frame = 0

        for subtitle in subtitles:
            subtitle_start_frame = Timecode.from_timedelta(subtitle.start, self.timecode_settings, False).get_frame(True)
            subtitle_end_frame = Timecode.from_timedelta(subtitle.end, self.timecode_settings, False).get_frame(True)

            if last_frame > subtitle_start_frame:  # skip overlap
                skipped_subtitles.append(subtitle)
                continue

            subtitle_infos.append(
                SubtitleInfo(
                    text_content=subtitle.content,
                    record_frame=subtitle_start_frame,
                    frames=subtitle_end_frame - subtitle_start_frame,
                )
            )

            last_frame = subtitle_end_frame

        log.info(f"Will insert {len(subtitle_infos)} clips")

        if len(skipped_subtitles) > 0:
            log.info(f"{len(skipped_subtitles)} subtitles will be skipped because of overlapping")
            log.debug(f"Skipped subtitles: {[subtitle.index for subtitle in skipped_subtitles]}")

        return subtitle_infos

    def create_subtitle_timeline(self, resolve_app: ResolveApp, subtitle_infos: list[SubtitleInfo]):
        frame_rate_name = str(self.timecode_settings.frame_rate).rstrip("0").rstrip(".")

        media_pool = resolve_app.get_media_pool()
        media_pool_textplus = media_pool.find_item(lambda item: item.GetClipProperty("Clip Name") == f"Text+{frame_rate_name}fps")

        log.info("Creating subtitle timeline...")
        log.flush()

        timeline_to_copy = resolve_app.find_timeline(f"Timeline{frame_rate_name}fps")
        timeline_name = f"AutoSubtitle_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        timeline = timeline_to_copy.DuplicateTimeline(timeline_name)

        if timeline is None:
            log.error(f"Failed to create timeline '{timeline_name}'")
            return None

        log.info("Adding clips...")
        log.flush()

        timeline_items = resolve_app.media_pool.AppendToTimeline(
            [
                {
                    "mediaPoolItem": media_pool_textplus,
                    "startFrame": 0,
                    "endFrame": subtitle_info.frames,
                    "recordFrame": subtitle_info.record_frame,
                }
                for subtitle_info in subtitle_infos
            ]
        )

        expected_clip_count = len(subtitle_infos)
        clip_count = len(timeline_items)

        if expected_clip_count != clip_count:
            log.warning(f"Unexpected result when inserting clips. Expect {expected_clip_count} clips added, get {clip_count}")

        log.info(f"Setting {clip_count} clips content...")

        for subtitle_info, timeline_item in zip(subtitle_infos, timeline_items):
            textplus = textplus_utils.find_textplus(timeline_item)
            textplus.SetInput("StyledText", subtitle_info.text_content)

        return timeline
