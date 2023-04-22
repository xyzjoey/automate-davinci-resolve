from typing import Optional

from pydantic import BaseModel, Field

from .action_base import ActionBase
from ..inputs.tracks import MultipleVideoTracksInput
from ...davinci import textplus_utils
from ...davinci.context import TimelineDiff
from ...davinci.enums import ResolveStatus
from ...davinci.resolve_app import ResolveApp


class Inputs(BaseModel):
    ignored_tracks: MultipleVideoTracksInput = Field([], title="Ignored Video Tracks")


class Action(ActionBase):
    def __init__(self):
        super().__init__(
            name="auto_textplus_style",
            display_name="Auto Text+ Style",
            description="Detect newly added Text+ clips and apply style to them, using the style of 1st Text+ clip in the same track.",
            required_status=ResolveStatus.TimelineOpened,
            input_model=Inputs,
        )

    def update(
        self,
        resolve_app: ResolveApp,
        timeline_diff: Optional[TimelineDiff],
        input_data: Inputs,
    ):
        if timeline_diff is None:
            return

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
            reference_textplus_data = None

            for item in track.timeline_items:
                if reference_textplus_data is None:
                    reference_textplus_data = textplus_utils.get_textplus_data(item)
                elif item.GetUniqueId() in newly_added_item_ids:
                    textplus_utils.set_textplus_data_only_style(item, reference_textplus_data)
