from ..resolve_types import PyRemoteTimelineItem
from ..utils.math import FrameRange
from .media_pool_item import MediaPoolItem
from .track import TrackHandle


class TimelineItem:
    def __init__(self, _item: PyRemoteTimelineItem):
        self._item = _item

    def get_track_handle(self):
        track_type, index = self._item.GetTrackTypeAndIndex()

        return TrackHandle(track_type, index)

    def get_frame_range(self):
        return FrameRange(self._item.GetStart(), self._item.GetEnd())

    def get_media_pool_item(self):
        _media_pool_item = self._item.GetMediaPoolItem()

        return MediaPoolItem(_media_pool_item) if _media_pool_item is not None else None

    def get_last_fusion_composition(self):
        comp_count = self._item.GetFusionCompCount()

        if comp_count == 0:
            return None

        return self._item.GetFusionCompByIndex(comp_count)
