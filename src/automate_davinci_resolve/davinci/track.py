from .context import TrackContext, TimelineItemContext


class Track:
    def __init__(self, track_name: str, track_type: str, track_index: int, timeline_items: list):
        self.name = track_name
        self.type = track_type
        self.index = track_index
        self.timeline_items = timeline_items

    def __repr__(self):
        return f"Track({self.type}, {self.index}, {self.name})"

    def capture_context(self):
        return TrackContext(
            index=self.index,
            name=self.name,
            items={item.GetUniqueId(): TimelineItemContext(id=item.GetUniqueId()) for item in self.timeline_items},
        )
