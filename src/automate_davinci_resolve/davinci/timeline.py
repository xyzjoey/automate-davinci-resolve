from .timecode import Timecode, TimecodeSettings
from .track import Track
from .context import TimelineContext


class Timeline:
    def __init__(self, timeline):
        self.timeline = timeline

    def __repr__(self):
        return f"Timeline({self.timeline.GetName()})"

    def get_current_item_at_track(self, track_type: str, track_index: int):
        timecode_settings = self.get_timecode_settings()

        current_frame = Timecode.from_str(self.timeline.GetCurrentTimecode(), timecode_settings, True).get_frame(True)

        for item in self.timeline.GetItemListInTrack(track_type, track_index):
            if (item.GetStart() <= current_frame) and (current_frame < item.GetEnd()):
                return item

        return None

    def has_track(self, track_type: str, track_index: int):
        track_count = self.timeline.GetTrackCount(track_type)
        return 1 <= track_index and track_index <= track_count

    def get_track(self, track_type: str, track_index: int):
        if not self.has_track(track_type, track_index):
            return None

        track_name = self.timeline.GetTrackName(track_type, track_index)
        items = self.timeline.GetItemListInTrack(track_type, track_index)

        return Track(track_name, track_type, track_index, list(items))

    def iter_tracks(self, track_type):
        track_count = self.timeline.GetTrackCount(track_type)

        for i in range(1, track_count + 1):
            yield self.get_track(track_type, i)

    def get_timecode_settings(self):
        return TimecodeSettings(self.timeline.GetStartTimecode(), float(self.timeline.GetSetting("timelineFrameRate")))

    def capture_context(self):
        return TimelineContext(
            id=self.timeline.GetUniqueId(),
            name=self.timeline.GetName(),
            video_tracks={track.index: track.capture_context() for track in self.iter_tracks("video")},
        )
