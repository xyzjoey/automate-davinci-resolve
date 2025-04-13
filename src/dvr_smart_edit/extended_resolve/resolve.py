from contextlib import contextmanager
from typing import NamedTuple

from ..extended_resolve.constants import MediaPoolItemType
from ..extended_resolve.track import TrackHandle
from ..resolve_types import PyRemoteResolve
from .media_pool import MediaPool
from .media_pool_item import MediaPoolItem
from .timecode import TimecodeUtils
from .timeline import Timeline
from .timeline_item import TimelineItem


class MediaPoolItemInsertInfo(NamedTuple):
    media_pool_item: MediaPoolItem
    start_frame: int
    end_frame: int | None = None
    frames: int | None = None
    source_start_frame: float = 0.0
    track_handle: TrackHandle | None = None


class Resolve:
    def __init__(self, _resolve: "PyRemoteResolve"):
        self._resolve = _resolve
        self._project_manager = self._resolve.GetProjectManager()

    def get_current_project(self):
        return self._project_manager.GetCurrentProject()

    def get_current_timeline(self):
        return Timeline(self.get_current_project().GetCurrentTimeline())

    def get_media_pool(self):
        return MediaPool(self.get_current_project().GetMediaPool())

    def get_ui_manager(self):
        pass

    @contextmanager
    def temp_timeline_item(self, media_pool_item: MediaPoolItem, start_frame=None, end_frame=None):
        timeline = self.get_current_timeline()

        timecode = timeline.get_current_timecode()
        start_frame = start_frame or timecode.get_frame(True)

        item_fps = media_pool_item.get_frame_rate()
        timeline_fps = timeline.get_frame_rate()
        min_frames = max(TimecodeUtils.timedelta_to_frame(TimecodeUtils.frame_to_timedelta(1, item_fps), timeline_fps), 1)

        with timeline.temp_track("video") as track_handle:
            timeline_items = self.insert_to_timeline(
                [
                    MediaPoolItemInsertInfo(
                        media_pool_item=media_pool_item,
                        start_frame=start_frame,
                        end_frame=end_frame,
                        frames=min_frames if end_frame is None else None,
                        track_handle=track_handle,
                    )
                ]
            )
            timeline_item = timeline_items[0]

            yield timeline_item

            if timeline_item is not None:
                timeline.delete_items([timeline_item])

    def insert_to_timeline(self, insert_infos: list[MediaPoolItemInsertInfo], auto_unlock=True):
        MEDIA_TYPE_MAP = {"video": 1, "audio": 2}

        timeline = self.get_current_timeline()
        timeline_fps = timeline.get_frame_rate()

        resolve_clip_infos = []

        for insert_info in insert_infos:
            item_fps = insert_info.media_pool_item.get_frame_rate()
            mark_in_out = insert_info.media_pool_item._item.GetMarkInOut()
            mark_in = mark_in_out.get(insert_info.track_handle.type, {}).get("in")
            mark_out = mark_in_out.get(insert_info.track_handle.type, {}).get("out")

            source_start_frame = insert_info.source_start_frame
            source_frames = TimecodeUtils.frame_to_frame(insert_info.frames or insert_info.end_frame - insert_info.start_frame, timeline_fps, item_fps)

            if mark_in is not None:
                source_start_frame = max(source_start_frame, mark_in)

            if mark_out is not None:
                source_frames = min(source_frames, mark_out)

            if not MediaPoolItemType.support_extending_duration(insert_info.media_pool_item.get_clip_type()):
                source_frames = min(source_frames, insert_info.media_pool_item.get_duration())

            resolve_clip_info = {
                "mediaPoolItem": insert_info.media_pool_item._item,
                "startFrame": source_start_frame,
                "endFrame": source_start_frame + source_frames,
                "recordFrame": insert_info.start_frame,
            }

            if insert_info.track_handle is not None:
                resolve_clip_info["mediaType"] = MEDIA_TYPE_MAP[insert_info.track_handle.type]
                resolve_clip_info["trackIndex"] = insert_info.track_handle.index

            resolve_clip_infos.append(resolve_clip_info)

        track_handles_to_unlock = set(insert_info.track_handle for insert_info in insert_infos if insert_info.track_handle is not None) if auto_unlock else []

        with timeline.temp_unlock_tracks(*track_handles_to_unlock):
            inserted_items = self.get_media_pool()._media_pool.AppendToTimeline(resolve_clip_infos)
            return [TimelineItem(item) if item is not None else None for item in inserted_items]
