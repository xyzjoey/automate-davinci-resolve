from typing import Optional

from ..context import InputContext
from ...davinci.context import TimelineDiff


class MultipleVideoTracksInput(list[int]):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        try:
            input_tracks = set((int(i) for i in v))
        except:
            raise ValueError(f"{v} is not a list of integer")

        if len(input_tracks) == 0:
            return cls(input_tracks)

        if InputContext.get() is None or InputContext.get().timeline_context is None:
            raise ValueError(f"No available tracks now")

        existing_tracks = list(InputContext.get().timeline_context.video_tracks.keys())
        invalid_tracks = input_tracks - set(existing_tracks)

        if invalid_tracks:
            raise ValueError(f"{invalid_tracks} are invalid track indices. Possible values: {existing_tracks}")

        final_tracks = cls(input_tracks)
        final_tracks.sort()

        return final_tracks

    # TODO keep data for different timeline
    def update(self, timeline_diff: Optional[TimelineDiff]):
        if timeline_diff is None:
            self.clear()
            return

        old_indices = self.copy()
        self.clear()

        for old_index in old_indices:
            new_index = timeline_diff.get_new_track_index(old_index)

            if new_index is not None:
                self.append(new_index)

        self.sort()
