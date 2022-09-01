class TrackContext:
    def __init__(self, track_name: str, track_type: str, track_index: int, timeline_items: list):
        self.track_name = track_name
        self.track_type = track_type
        self.track_index = track_index
        self.timeline_items = timeline_items

    def __repr__(self):
        return f"TrackContext({self.track_type}, {self.track_index}, {self.track_name})"
