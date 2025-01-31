from typing import Optional

from ...davinci.context import TimelineContext, TimelineDiff
from .checkbox_collection import CheckboxCollection, CheckboxOption


class MultipleVideoTracksWidget(CheckboxCollection):
    def update(
        self,
        timeline_context: Optional[TimelineContext],
        timeline_diff: Optional[TimelineDiff],
    ):
        if timeline_context is None:
            self.reset([])
            return

        options = {
            track_context.index: CheckboxOption(
                value=track_context.index,
                name=f"[{track_context.index}] {track_context.name}",
                selected=False,
            )
            for track_context in timeline_context.video_tracks.values()
        }

        if timeline_diff is not None:
            for prev_option in self.options:
                if prev_option.selected:
                    new_index = timeline_diff.get_new_track_index(prev_option.value)

                    if new_index is not None:
                        options[new_index].selected = True

        self.reset(options=list(options.values()))
