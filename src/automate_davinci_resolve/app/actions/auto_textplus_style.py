from typing import Optional

from pydantic import BaseModel, Field

from .action_base import ActionBase
from ..inputs.tracks import MultipleVideoTracksInput
from ..settings import AppSettings
from ...davinci import textplus_utils
from ...davinci.context import TimelineDiff
from ...davinci.enums import ResolveStatus
from ...davinci.resolve_app import ResolveApp
from ...utils import log


class Inputs(BaseModel):
    ignored_tracks: MultipleVideoTracksInput = Field([], title="Ignored Video Tracks")


class Action(ActionBase):
    def __init__(self):
        super().__init__(
            name="auto_textplus_style",
            display_name="Auto Text+ Style",
            description="Detect newly added Text+ clips and apply style to them, using the style of 1st Text+ clip in the same track.",
            required_status=ResolveStatus.TimelineOpen,
            input_model=Inputs,
        )

    def update(
        self,
        app_settings: AppSettings,
        resolve_app: ResolveApp,
        timeline_diff: Optional[TimelineDiff],
        input_data: Inputs,
    ):
        if timeline_diff is None:
            return

        textplus_settings_path = f"{app_settings.temp_dir}/{self.name}.setting"

        # no need to check items in newly added track (diff["added"]["video_tracks"]["root"])
        # becuz high chance items are moved from same track

        for old_track_index, track_diff in timeline_diff.diff.get("added", {}).get("video_tracks", {}).items():
            if old_track_index == "root":
                continue

            new_track_index = timeline_diff.get_new_track_index(old_track_index)
            newly_added_item_ids = track_diff.get("items", {}).get("root", set())

            if new_track_index is None:
                continue

            if new_track_index in input_data.ignored_tracks:
                continue

            if len(newly_added_item_ids) == 0:
                continue

            track = resolve_app.get_current_timeline().get_track("video", new_track_index)
            reference_textplus = None

            for item in track.timeline_items:
                if reference_textplus is None:
                    reference_textplus = textplus_utils.find_textplus(item)
                    if reference_textplus is not None:
                        if not textplus_utils.save_settings(reference_textplus, textplus_settings_path):
                            log.warning(f"[{self}] Failed to save reference Text+ settings to '{textplus_settings_path}'. Skip track.")
                            break

                elif item.GetUniqueId() in newly_added_item_ids:
                    textplus = textplus_utils.find_textplus(item)
                    if textplus is not None:
                        textplus_utils.load_settings(textplus, textplus_settings_path, exclude_data_ids=["StyledText"])
