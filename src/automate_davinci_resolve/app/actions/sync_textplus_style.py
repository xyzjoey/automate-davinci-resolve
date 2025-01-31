from pydantic import BaseModel, Field

from ...davinci import textplus_utils
from ...davinci.enums import ResolveStatus
from ...davinci.resolve_app import ResolveApp
from ...utils import log
from ..inputs.tracks import MultipleVideoTracksInput
from ..settings import AppSettings
from .action_base import ActionBase


class Inputs(BaseModel):
    tracks: MultipleVideoTracksInput = Field([], title="Video Tracks")


class Action(ActionBase):
    def __init__(self):
        super().__init__(
            name="sync_textplus_style",
            display_name="Sync Text+ Style",
            description="Synchronize Text+ style of selected track(s), using the style of 1st Text+ clip in the same track.",
            required_status=ResolveStatus.TimelineOpen,
            input_model=Inputs,
        )

    def start(
        self,
        app_settings: AppSettings,
        resolve_app: ResolveApp,
        input_data: Inputs,
    ):
        if len(input_data.tracks) == 0:
            log.warning(f"[{self}] No tracks are selected")
            return

        textplus_settings_path = f"{app_settings.temp_dir}/{self.name}.setting"
        current_timeline = resolve_app.get_current_timeline()

        for track in current_timeline.iter_tracks("video"):
            if track.index not in input_data.tracks:
                continue

            log.info(f"[{self}] Finding Text+ in track {track.index}...")
            log.flush()

            textplus_list = []

            for item in track.timeline_items:
                textplus = textplus_utils.find_textplus(item)
                if textplus is not None:
                    textplus_list.append(textplus)

            log.info(f"[{self}] Found {len(textplus_list)} Text+. Start sync...")
            log.flush()

            if len(textplus_list) > 0:
                if not textplus_utils.save_settings(textplus_list[0], textplus_settings_path):
                    log.warning(f"[{self}] Failed to save reference Text+ settings to '{textplus_settings_path}'. Skip track.")
                    continue

            for i, textplus in enumerate(textplus_list[1:]):
                if not textplus_utils.load_settings(textplus, textplus_settings_path, exclude_data_ids=["StyledText"]):
                    log.warning(f"[{self}] Failed to load settings for {i}-th Text+ clip")

                if i > 0 and i % 50 == 0:
                    log.info(f"[{self}] Track {track.index} sync progress {i}/{len(textplus_list) - 1}...")
                    log.flush()

            log.info(f"[{self}] Successfully synchronize Text+ style for track {track.index}!")

        log.info(f"[{self}] Successfully synchronize Text+ style for tracks {input_data.tracks}!")
