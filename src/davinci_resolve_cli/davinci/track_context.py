class TrackContext:
    def __init__(self):
        self.name = None
        self.type = None
        self.index = None
        self.items = None

    @classmethod
    def get(cls, timeline, track_type, track_index) -> "TrackContext":
        track_context = cls()
        track_context.name = timeline.GetTrackName(track_type, track_index)
        track_context.type = track_type
        track_context.index = track_index

        items = timeline.GetItemListInTrack(track_type, track_index)

        if items is None:
            return None

        track_context.items = list(items)

        return track_context
