from typing import Optional

from pydantic_core.core_schema import no_info_after_validator_function

from ..context import InputContext
from ...davinci.context import TimelineDiff


class VideoTrackValidator:
    @classmethod
    def is_valid(self, *tracks):
        if len(tracks) == 0:
            return True, None

        if InputContext.get() is None or InputContext.get().timeline_context is None:
            return False, "No available tracks now"

        existing_tracks = list(InputContext.get().timeline_context.video_tracks.keys())
        invalid_tracks = set(tracks) - set(existing_tracks)

        if len(invalid_tracks) > 0:
            return False, f"{invalid_tracks} are invalid track indices. Possible values: {existing_tracks}"

        return True, None


class MultipleVideoTracksInput(list[int]):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return no_info_after_validator_function(cls.validate, handler(list[int]))

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        try:
            input_tracks = [int(i) for i in v]
        except:
            raise ValueError(f"{v} is not a list of integer")

        is_valid, reason = VideoTrackValidator.is_valid(*input_tracks)

        if is_valid:
            final_tracks = cls(input_tracks)
            final_tracks.sort()

            return final_tracks
        else:
            raise ValueError(reason)

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


# class SingleVideoTrackInput:


#     @classmethod
#     def __get_validators__(cls):
#         yield cls.validate

#     @classmethod
#     def validate(cls, v):
#         if isinstance(v, cls):
#             return v

#         try:
#             input_track = int(v)
#         except:
#             raise ValueError(f"{v} is not an integer")

#         is_valid, reason = VideoTrackValidator.is_valid(input_track)

#         if is_valid:
#             return cls(input_track)
#         else:
#             raise ValueError(reason)

#     # TODO keep data for different timeline
#     def update(self, timeline_diff: Optional[TimelineDiff]):
#         if timeline_diff is None:
#             self.clear()
#             return

#         old_indices = self.copy()
#         self.clear()

#         for old_index in old_indices:
#             new_index = timeline_diff.get_new_track_index(old_index)

#             if new_index is not None:
#                 self.append(new_index)

#         self.sort()
