from typing import Any

from .input_base import InputBase
from ..davinci.resolve_app import ResolveContext
from ..utils import terminal_io


class CurrentClipInput(InputBase[Any]):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        try:
            track_index = int(v)
        except:
            raise ValueError(f"{v} is not a valid integer")

        resolve_context = ResolveContext.get()
        timeline_context = resolve_context.get_current_timeline_context()
        track_count = timeline_context.timeline.GetTrackCount("video")

        if not timeline_context.has_track("video", track_index):
            raise ValueError(f"'{track_index}' is out of currently available tracks (1 to {track_count})")

        timeline_item = timeline_context.get_current_item_at_track("video", track_index)

        if timeline_item is None:
            raise ValueError(f"No clip at playhead position in video track {track_index}")

        return cls(timeline_item)

    @classmethod
    def ask_raw_input(cls):
        track_index = terminal_io.prompt(f"Please enter a video track index (start from 1) for getting current clip: ")
        return track_index
