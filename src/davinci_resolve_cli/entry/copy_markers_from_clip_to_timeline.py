from pydantic import BaseSettings, Field

from davinci_resolve_cli.action.action_base import ActionBase, ActionResult
from davinci_resolve_cli.davinci.timecode import Timecode
from davinci_resolve_cli.inputs.current_clip_input import CurrentClipInput
from davinci_resolve_cli.utils import terminal_io


class Inputs(BaseSettings):
    current_clip: CurrentClipInput = Field(
        description="Clip for copying markers from. Enter track index to get clip at the track at playhead location",
        default_factory=lambda: CurrentClipInput.ask_input(),
    )


class Action(ActionBase):
    def __init__(self):
        super().__init__(input_model=Inputs)

    async def run_with_input(self, inputs: Inputs):
        timeline_context = self.resolve_context.get_current_timeline_context()
        timecode_context = timeline_context.get_timecode_context()

        item = inputs.current_clip.get()
        start_frame = Timecode.from_frame(item.GetStart(), timecode_context, start_timecode_applied=True).get_frame(apply_start_timecode=False)

        added_markers_count = 0

        terminal_io.print_info(f"Copying markers from Clip({item.GetName()}) to current timeline...")

        for frame_id, marker_info in item.GetMarkers().items():
            success = timeline_context.timeline.AddMarker(
                start_frame + frame_id,
                marker_info["color"],
                marker_info["name"],
                marker_info["note"],
                marker_info["duration"],
                marker_info["customData"],
            )

            if success:
                added_markers_count += 1
            else:
                terminal_io.print_warning(f"Failed to add marker {frame_id}: {marker_info}")

        terminal_io.print_info(f"Successfully added {added_markers_count} markers")

        return ActionResult.Done


if __name__ == "__main__":
    Action().main()

