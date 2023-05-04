from typing import Any, NamedTuple, Optional

from pydantic import BaseModel, Field

from .action_base import ActionBase
from ..inputs.tracks import MultipleVideoTracksInput
from ...davinci import textplus_utils
from ...davinci.context import TimelineDiff
from ...davinci.enums import ResolveStatus
from ...davinci.timecode import Timecode
from ...davinci.resolve_app import ResolveApp
from ...utils import log


class Inputs(BaseModel):
    ignored_tracks: MultipleVideoTracksInput = Field([], title="Ignored Video Tracks")


class ItemWithTextplus(NamedTuple):
    item: Any
    textplus: Any


class StylingContext(NamedTuple):
    reference: ItemWithTextplus
    targets: list[ItemWithTextplus]


class Action(ActionBase):
    def __init__(self):
        super().__init__(
            name="auto_textplus_style",
            display_name="Auto Text+ Style",
            description="Detect newly added Text+ clips and apply style to them, using the style of 1st Text+ clip in the same track.",
            required_status=ResolveStatus.TimelineOpened,
            input_model=Inputs,
        )

    def get_applicable_items(self, timeline, timeline_diff, ignored_tracks) -> dict[int, StylingContext]:
        styling_context_by_track = {}

        # no need to check items in newly added track (diff["added"]["video_tracks"]["__root__"])
        # becuz high chance items are already same style
        for old_track_index, track_diff in timeline_diff.diff.get("added", {}).get("video_tracks", {}).items():
            if old_track_index == "__root__":
                continue

            new_track_index = timeline_diff.get_new_track_index(old_track_index)
            newly_added_item_ids = track_diff.get("items", {}).get("__root__", set())

            if new_track_index is None:
                continue

            if len(newly_added_item_ids) == 0:
                continue

            if new_track_index in ignored_tracks:
                continue

            reference = None
            targets = []

            track = timeline.get_track("video", new_track_index)

            for item in track.timeline_items:
                if reference is None:
                    textplus = textplus_utils.find_textplus(item)
                    if textplus is not None:
                        reference = ItemWithTextplus(item, textplus)

                elif item.GetUniqueId() in newly_added_item_ids:
                    textplus = textplus_utils.find_textplus(item)
                    if textplus is not None:
                        targets.append(ItemWithTextplus(item, textplus))

            if reference is not None and len(targets) > 0:
                styling_context_by_track[new_track_index] = StylingContext(reference, targets)

        return styling_context_by_track

    def update(
        self,
        resolve_app: ResolveApp,
        timeline_diff: Optional[TimelineDiff],
        input_data: Inputs,
    ):
        if timeline_diff is None:
            return

        timeline = resolve_app.get_current_timeline()
        timecode_settings = timeline.get_timecode_settings()

        as_str = (
            lambda item_with_textplus: f"(start={Timecode.from_frame(item_with_textplus.item.GetStart(), timecode_settings, True).get_str(True)}, text={repr(item_with_textplus.textplus.GetInput('StyledText'))})"
        )

        styling_context_by_track = self.get_applicable_items(timeline, timeline_diff, input_data.ignored_tracks)

        for track_index, styling_context in styling_context_by_track.items():
            reference_settings = textplus_utils.get_settings(styling_context.reference.textplus)

            if reference_settings is None:
                log.warning(f"[{self}] Failed to get settings from Text+ reference {as_str(styling_context.reference)}. Skip track {track_index}.")
                continue

            for target in styling_context.targets:
                if not textplus_utils.set_settings(target.textplus, reference_settings, exclude=["StyledText"]):
                    log.warning(f"[{self}] Failed to update Text+ clip {as_str(target)}")
