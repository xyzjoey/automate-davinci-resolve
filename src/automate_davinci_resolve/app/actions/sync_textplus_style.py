from typing import Any, NamedTuple

from pydantic import BaseModel, Field

from .action_base import ActionBase
from ..inputs.tracks import MultipleVideoTracksInput
from ...davinci import textplus_utils
from ...davinci.enums import ResolveStatus
from ...davinci.timecode import Timecode
from ...davinci.resolve_app import ResolveApp
from ...utils import log


class Inputs(BaseModel):
    tracks: MultipleVideoTracksInput = Field([], title="Video Tracks")


class ItemWithTextplus(NamedTuple):
    item: Any
    textplus: Any


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
        resolve_app: ResolveApp,
        input_data: Inputs,
    ):
        if len(input_data.tracks) == 0:
            log.warning(f"[{self}] No tracks are selected")
            return

        current_timeline = resolve_app.get_current_timeline()
        timecode_settings = current_timeline.get_timecode_settings()

        as_str = lambda item, textplus: f"(start={Timecode.from_frame(item.GetStart(), timecode_settings, True).get_str(True)}, text={repr(textplus.GetInput('StyledText'))})"

        for track in current_timeline.iter_tracks("video"):
            if track.index not in input_data.tracks:
                continue

            log.info(f"[{self}] Finding Text+ in track {track.index}...")
            log.flush()

            items_with_textplus = []
            reference_settings = None

            for item in track.timeline_items:
                textplus = textplus_utils.find_textplus(item)
                if textplus is not None:
                    items_with_textplus.append(ItemWithTextplus(item, textplus))

            log.info(f"[{self}] Found {len(items_with_textplus)} Text+. Start sync...")
            log.flush()

            if len(items_with_textplus) > 0:
                item, reference_textplus = items_with_textplus[0]
                reference_settings = textplus_utils.get_settings(reference_textplus)
                if reference_settings is None:
                    log.warning(f"[{self}] Failed to get reference Text+ settings {as_str(item, reference_textplus)}. Skip track.")
                    continue

            for i, (item, textplus) in enumerate(items_with_textplus[1:]):
                if not textplus_utils.set_settings(textplus, reference_settings, exclude=["StyledText"]):
                    log.warning(f"[{self}] Failed to update Text+ clip {as_str(item, textplus)}")

                if i > 0 and i % 50 == 0:
                    log.info(f"[{self}] Track {track.index} sync progress {i}/{len(items_with_textplus) - 1}...")
                    log.flush()

            log.info(f"[{self}] Successfully synchronize Text+ style for track {track.index}!")

        if len(input_data.tracks) > 1:
            log.info(f"[{self}] Successfully synchronize Text+ style for tracks {input_data.tracks}!")
