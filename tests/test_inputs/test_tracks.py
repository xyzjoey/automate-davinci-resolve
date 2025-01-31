from pydantic import BaseModel, ValidationError

from automate_davinci_resolve.app.inputs.tracks import MultipleVideoTracksInput
from automate_davinci_resolve.app.context import InputContext
from automate_davinci_resolve.davinci.context import TimelineContext, TimelineDiff, TrackContext, Diff


class Input(BaseModel):
    tracks: MultipleVideoTracksInput


class TestTracksInput:
    def test_valid_input(self):
        InputContext.set(
            InputContext(
                TimelineContext(
                    id=...,
                    name=...,
                    video_tracks={
                        1: TrackContext(index=1, name=..., items={}),
                        2: TrackContext(index=2, name=..., items={}),
                        3: TrackContext(index=3, name=..., items={}),
                    },
                )
            )
        )

        assert Input.model_validate({"tracks": [1, 3]}).tracks == [1, 3]

    def test_invalid_input(self):
        InputContext.set(
            InputContext(
                TimelineContext(
                    id=...,
                    name=...,
                    video_tracks={
                        1: TrackContext(index=1, name=..., items={}),
                        2: TrackContext(index=2, name=..., items={}),
                    },
                )
            )
        )

        try:
            Input.model_validate({"tracks": [1, 3]})
            assert False
        except ValidationError:
            assert True

    def test_tracks_changed(self):
        tracks_input = MultipleVideoTracksInput([1, 3])

        diff = TimelineDiff()
        diff.diff = {
            "changed": {
                "video_tracks": {
                    2: {"index": Diff(old=2, new=1)},
                    3: {"index": Diff(old=3, new=2)},
                }
            },
            "removed": {"video_tracks": {"root": [1]}},
        }

        tracks_input.update(diff)

        assert tracks_input == [2]
