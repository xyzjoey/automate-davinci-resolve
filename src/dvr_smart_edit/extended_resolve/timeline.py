from contextlib import contextmanager
from typing import Callable, Iterable

from ..resolve_types import PyRemoteTimeline
from .timecode import Timecode, TimecodeSettings
from .timeline_item import TimelineItem
from .track import TrackHandle


class Timeline:
    def __init__(self, _timeline: PyRemoteTimeline):
        self._timeline = _timeline
        self.timecode_settings = None

    def __repr__(self):
        return f"Timeline({self._timeline.GetName()})"

    def get_current_timecode(self):
        timecode_settings = self.get_timecode_settings()
        return Timecode.from_str(self._timeline.GetCurrentTimecode(), timecode_settings, True)

    def find_current_item_in_track(self, track_handle: TrackHandle):
        current_frame = self.get_current_timecode().get_frame(True)

        for item in self._timeline.GetItemListInTrack(track_handle.type, track_handle.index):
            if (item.GetStart() <= current_frame) and (current_frame < item.GetEnd()):
                return TimelineItem(item)

        return None

    def iter_items_in_track(self, track_handle: TrackHandle, condition: Callable = lambda _: True):
        for _item in self._timeline.GetItemListInTrack(track_handle.type, track_handle.index):
            item = TimelineItem(_item)
            if condition(item):
                yield item

    def iter_items(self, condition: Callable = lambda _: True, track_type: str = None):
        track_types = ["video", "audio", "subtitle"] if track_type is None else [track_type]

        for curr_track_type in track_types:
            for track_handle in self.iter_tracks(curr_track_type):
                for item in self.iter_items_in_track(track_handle):
                    if condition(item):
                        yield (item)

    def find_item(self, condition: Callable, track_type: str = None):
        item = next((item for item in self.iter_items(condition, track_type)), None)

        return item

    def delete_items(self, items: Iterable[TimelineItem], auto_unlock=True):
        item_list = list(items)
        track_handles_to_unlock = set(item.get_track_handle() for item in item_list) if auto_unlock else []

        with self.temp_unlock_tracks(*track_handles_to_unlock):
            self._timeline.DeleteClips([item._item for item in item_list])

    def iter_tracks(self, track_type):
        track_count = self._timeline.GetTrackCount(track_type)

        for i in range(1, track_count + 1):
            yield TrackHandle(track_type, i)

    def find_track_by_name(self, track_type: str, track_name) -> TrackHandle | None:
        for track_handle in self.iter_tracks(track_type):
            if self._timeline.GetTrackName(track_handle.type, track_handle.index) == track_name:
                return track_handle

        return None

    def has_track(self, track_handle: TrackHandle):
        count = self._timeline.GetTrackCount(track_handle.type)
        return count >= track_handle.index

    def add_track(self, track_type: str, track_index=None):
        result = False

        if track_index is not None:
            result = self._timeline.AddTrack(track_type, {"index": track_index})
        else:
            result = self._timeline.AddTrack(track_type)

        if not result:
            return None

        if track_index is not None:
            return TrackHandle(track_type, track_index)
        else:
            return TrackHandle(track_type, self._timeline.GetTrackCount(track_type))

    def get_or_add_track_by_name(self, track_type: str, track_name: str, track_index: int = None):
        track_handle = self.find_track_by_name(track_type, track_name)

        if track_handle is not None:
            return track_handle

        track_handle = self.add_track(track_type, track_index)

        if track_handle is not None:
            self._timeline.SetTrackName(track_handle.type, track_handle.index, track_name)

        return track_handle

    def clear_track(self, track_handle: TrackHandle):
        items = list(self.iter_items_in_track(track_handle))
        self.delete_items(items)

    def get_track_enabled(self, track_handle: TrackHandle):
        return self._timeline.GetIsTrackEnabled(track_handle.type, track_handle.index)

    def set_track_enabled(self, track_handle: TrackHandle, enabled: bool):
        return self._timeline.SetTrackEnable(track_handle.type, track_handle.index, enabled)

    def get_track_locked(self, track_handle: TrackHandle):
        return self._timeline.GetIsTrackLocked(track_handle.type, track_handle.index)

    def set_track_locked(self, track_handle: TrackHandle, locked: bool):
        return self._timeline.SetTrackLock(track_handle.type, track_handle.index, locked)

    def get_frame_rate(self):
        return float(self._timeline.GetSetting("timelineFrameRate"))

    def get_timecode_settings(self):
        if self.timecode_settings is None:
            self.timecode_settings = TimecodeSettings(self._timeline.GetStartTimecode(), self.get_frame_rate())

        return self.timecode_settings

    def get_item_start_timecode(self, item: TimelineItem):
        return Timecode.from_frame(item._item.GetStart(), self.get_timecode_settings(), True)

    def get_item_end_timecode(self, item: TimelineItem):
        return Timecode.from_frame(item._item.GetEnd(), self.get_timecode_settings(), True)

    @contextmanager
    def temp_unlock_tracks(self, *track_handles: list[TrackHandle]):
        is_locked_list = []

        for track_handle in track_handles:
            is_locked = self.get_track_locked(track_handle)
            is_locked_list.append(is_locked)

            if is_locked:
                self.set_track_locked(track_handle, False)

        yield

        for i, track_handle in enumerate(track_handles):
            if is_locked_list[i]:
                self.set_track_locked(track_handle, True)

    @contextmanager
    def temp_track(self, track_type: str):
        track_handle = self.add_track(track_type)

        try:
            yield track_handle
        finally:
            if track_handle is not None:
                self._timeline.DeleteTrack(track_handle.type, track_handle.index)

    @contextmanager
    def rollback_playhead_on_exit(self):
        playhead = self._timeline.GetCurrentTimecode()

        yield

        self._timeline.SetCurrentTimecode(playhead)
