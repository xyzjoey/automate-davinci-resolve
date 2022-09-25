class TrackContext:
    def __init__(self, track_name: str, track_type: str, track_index: int, timeline_items: list):
        self.name = track_name
        self.type = track_type
        self.index = track_index
        self.timeline_items = timeline_items

    def __repr__(self):
        return f"TrackContext({self.type}, {self.index}, {self.name})"
