from pydantic import BaseModel, Field, validator

from .action_base import ActionBase
from ..inputs.tracks import MultipleVideoTracksInput

# from ..inputs.tracks import SingleVideoTrackInput
from ...davinci import textplus_utils
from ...davinci.enums import ResolveStatus
from ...davinci.resolve_app import ResolveApp
from ...utils import log


class Inputs(BaseModel):
    track: int
    # track: MultipleVideoTracksInput = Field([], title="Video Track")


class Action(ActionBase):
    def __init__(self):
        super().__init__(
            name="print_clip_info",
            display_name="Print Clip Info",
            description="Print information of the clip in chosen track and at current playhead position",
            required_status=ResolveStatus.TimelineOpen,
            input_model=Inputs,
        )

    def start(
        self,
        resolve_app: ResolveApp,
        input_data: Inputs,
    ):
        track_index = input_data.track

        # if input_data.track is None:
        #     log.warning(f"[{self}] Track is not provided")

        current_timeline = resolve_app.get_current_timeline()

        item = current_timeline.get_current_item_at_track("video", track_index)

        if item is None:
            log.warning(f"[{self}] No clip found at current playhead in track {track_index}")

        textplus = textplus_utils.find_textplus(item)

        log.info(f"[{self}] Clip found:")
        log.info(f"[{self}] {item.GetName()}")
        # log.info(f"[{self}] {textplus_utils.get_textplus_data(item)}")

        for input in textplus.GetInputList().values():
            input_id = input.GetAttrs("INPS_ID")

            if input.GetAttrs("INPS_DataType") != "Gradient":
                continue

            # if input_id != "Start" and input_id != "End":
            #     continue

            value = textplus.GetInput(input_id)

            log.info(f"input_id={input_id}")
            log.info(f"value={value}")
            log.info(f"input.GetExpression()={input.GetExpression()}")
            log.info(f"{input.GetAttrs()}")
