from datetime import datetime
import os
from typing import Optional, NamedTuple

from pydantic import BaseModel, Field
import srt

from .action_base import ActionBase
from ..inputs.subtitles import SubtitleFileInput
from ..settings import AppSettings
from ...davinci.enums import ClipColor
from ...davinci import textplus_utils
from ...davinci.enums import ResolveStatus
from ...davinci.resolve_app import ResolveApp
from ...davinci.timecode import Timecode, TimecodeSettings
from ...utils import log


class Inputs(BaseModel):
    subtitle_file: SubtitleFileInput = Field(title="Subtitle File")
    gap_filler_clip_color: Optional[ClipColor] = Field(None, title="GapFiller Clip Color")


class SubtitleInsertInfo(NamedTuple):
    text_content: Optional[str]
    frames: int


class SubtitleInsertContext(NamedTuple):
    frame_rate: float
    infos: list[SubtitleInsertInfo]


class Action(ActionBase):
    frame_rate: float = 60

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
        datetime_formatted = datetime.now().strftime("%Y%m%d%H%M%S")
        subtitle_project_path = f"{app_settings.data_dir}/auto_subtitle.drp"
        temp_timeline_path = f"{app_settings.temp_dir}/auto_subtitles_{datetime_formatted}.drt"

        with resolve_app.import_temp_project(
            subtitle_project_path,
            project_name=f"auto_subtitle_{datetime_formatted}",
            log_prefix=f"[{self}] ",
        ) as project:
            if project is None:
                return

            subtitle_insert_context = self.prepare_subtitle_insert_context(resolve_app, input_data.subtitle_file.parsed)
            timeline = self.create_subtitle_timeline(resolve_app, input_data, subtitle_insert_context)

            if timeline is None:
                return

            result = timeline.Export(temp_timeline_path, resolve_app.resolve.EXPORT_DRT, resolve_app.resolve.EXPORT_NONE)

            if not result:
                log.error(f"[{self}] Failed to export timeline to {temp_timeline_path}")
                return

        timeline = resolve_app.media_pool.ImportTimelineFromFile(temp_timeline_path)

        if timeline is None:
            log.error(f"[{self}] Failed to import timeline from {temp_timeline_path}")
            return

        log.info(f"[{self}] Successfully created subtitle timeline '{timeline.GetName()}'!")

        os.remove(temp_timeline_path)

    def prepare_subtitle_insert_context(self, resolve_app: ResolveApp, subtitles: list[srt.Subtitle]):
        timecode_settings = TimecodeSettings("01:00:00:00", self.frame_rate)

        subtitle_insert_context = SubtitleInsertContext(frame_rate=timecode_settings.frame_rate, infos=[])
        skipped_subtitles = []

        last_frame = 0

        for subtitle in subtitles:
            subtitle_start_frame = Timecode.from_timedelta(subtitle.start, timecode_settings, False).get_frame(False)
            subtitle_end_frame = Timecode.from_timedelta(subtitle.end, timecode_settings, False).get_frame(False)

            if last_frame > subtitle_start_frame:  # skip overlap
                skipped_subtitles.append(subtitle)
                continue

            if last_frame < subtitle_start_frame:  # there is gap
                subtitle_insert_context.infos.append(
                    SubtitleInsertInfo(
                        text_content=None,
                        frames=(subtitle_start_frame - last_frame),
                    )
                )
                last_frame = subtitle_start_frame

            subtitle_insert_context.infos.append(
                SubtitleInsertInfo(
                    text_content=subtitle.content,
                    frames=(subtitle_end_frame - last_frame),
                )
            )

            last_frame = subtitle_end_frame

        clip_count = len(subtitle_insert_context.infos)
        subtitle_clip_count = sum(1 for info in subtitle_insert_context.infos if info.text_content is not None)
        gap_filler_count = clip_count - subtitle_clip_count

        log.info(f"[{self}] Will insert ({subtitle_clip_count} Text+) + ({gap_filler_count} GapFiller) = {clip_count} clips")

        if len(skipped_subtitles) > 0:
            log.info(f"[{self}] {len(skipped_subtitles)} subtitles will be skipped because of overlapping")
            log.debug(f"[{self}] Skipped subtitles: {[subtitle.index for subtitle in skipped_subtitles]}")

        return subtitle_insert_context

    def create_subtitle_timeline(self, resolve_app: ResolveApp, input_data: Inputs, subtitle_insert_context: SubtitleInsertContext):
        clip_count = len(subtitle_insert_context.infos)

        media_pool = resolve_app.get_media_pool()
        media_pool_textplus = media_pool.find_item(lambda item: item.GetClipProperty("Clip Name") == f"Text+{self.frame_rate}fps")
        media_pool_gapfiller = media_pool.find_item(lambda item: item.GetClipProperty("Clip Name") == f"GapFiller{self.frame_rate}fps")
        # media_pool_gapfiller.SetClipColor(input_data.gap_filler_clip_color.value)  # no effect

        log.info(f"[{self}] Creating subtitle timeline with {clip_count} clips...")
        log.flush()

        timeline_to_copy = resolve_app.fine_timeline(f"Timeline{self.frame_rate}fps")
        timeline_name = f"AutoSubtitle_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        timeline = timeline_to_copy.DuplicateTimeline(timeline_name)

        if timeline is None:
            log.error(f"[{self}] Failed to create timeline '{timeline_name}'")
            return None

        # below line has no effect, use project frame rate ("timelineFrameRate" is read-only?)
        # timeline.SetSetting("timelineFrameRate", str(subtitle_insert_context.frame_rate))

        timeline_items = resolve_app.media_pool.AppendToTimeline(
            [
                {
                    "mediaPoolItem": media_pool_textplus if insert_info.text_content is not None else media_pool_gapfiller,
                    "startFrame": 0,
                    "endFrame": insert_info.frames,
                }
                for insert_info in subtitle_insert_context.infos
            ]
        )

        # below line does not work. CreateTimelineFromClips cannot add same clip twice?
        # timeline = resolve_app.media_pool.CreateTimelineFromClips("AutoSubtitle", clip_infos)

        if clip_count != len(timeline_items):
            log.warning(f"[{self}] Unexpected result when inserting clips. Expect {clip_count} clips added, get {len(timeline_items)}")

        log.info(f"[{self}] Setting {len(timeline_items)} clips content...")

        for i, (insert_info, timeline_item) in enumerate(zip(subtitle_insert_context.infos, timeline_items)):
            # log.info(f"[{self}] Setting clip content ({i + 1}/{len(timeline_items)})...", end="\r")

            if insert_info.text_content is not None:
                textplus = textplus_utils.find_textplus(timeline_item)
                textplus.SetInput("StyledText", insert_info.text_content)
            elif input_data.gap_filler_clip_color is not None:
                timeline_item.SetClipColor(input_data.gap_filler_clip_color.value)

        return timeline
