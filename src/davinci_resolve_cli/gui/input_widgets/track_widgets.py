from typing import Optional

from .checkbox_collection import CheckboxCollection, CheckboxOption

from ...davinci.context import TimelineContext


class MultipleVideoTracksWidget(CheckboxCollection):
    def update(
        self,
        timeline_context: Optional[TimelineContext],
        input_data: Optional[list[int]],
    ):
        if timeline_context is None:
            self.reset([])
            return

        self.reset(
            options=[
                CheckboxOption(
                    value=track_context.index,
                    name=f"[{track_context.index}] {track_context.name}",
                    selected=(track_context.index in input_data) if input_data is not None else False,
                )
                for track_context in timeline_context.video_tracks.values()
            ]
        )
