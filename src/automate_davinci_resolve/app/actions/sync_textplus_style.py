from pydantic import BaseModel, Field, validator

from .action_base import ActionBase
from ..inputs.tracks import MultipleVideoTracksInput
from ...davinci import textplus_utils
from ...davinci.enums import ResolveStatus
from ...davinci.resolve_app import ResolveApp
from ...utils import log


class Inputs(BaseModel):
    tracks: MultipleVideoTracksInput = Field([], title="Video Tracks")


class Action(ActionBase):
    def __init__(self):
        super().__init__(
            name="sync_textplus_style",
            display_name="Sync Text+ Style",
            description="Synchronize Text+ style of selected track(s), using the style of 1st Text+ clip in the same track.",
            required_status=ResolveStatus.TimelineOpened,
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

        for track in current_timeline.iter_tracks("video"):
            if track.index in input_data.tracks:
                reference_textplus_data = None

                for item in track.timeline_items:
                    if reference_textplus_data is None:
                        reference_textplus_data = textplus_utils.get_textplus_data(item)
                    else:
                        textplus_utils.set_textplus_data_only_style(item, reference_textplus_data)

        log.info(f"[{self}] Successfully synchronize Text+ style for tracks {input_data.tracks}!")
