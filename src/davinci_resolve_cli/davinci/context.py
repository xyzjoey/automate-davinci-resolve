from typing import Any, NamedTuple, Optional

from .enums import ResolveStatus


class TimelineItemContext(NamedTuple):
    id: str


class TrackContext(NamedTuple):
    index: int
    name: str
    items: dict[str, TimelineItemContext]


class TimelineContext(NamedTuple):
    id: str
    name: str
    video_tracks: dict[int, TrackContext]


class ResolveContext(NamedTuple):
    resolve_status: ResolveStatus
    timeline_context: Optional[TimelineContext]
    timeline_diff: Optional["TimelineDiff"]


class Diff(NamedTuple):
    old: Any
    new: Any


class TimelineDiff:
    def __init__(self):
        self.diff = {}

    @classmethod
    def create(cls, old_timeline_context: Optional[TimelineContext], new_timeline_context: TimelineContext):
        diff = TimelineDiff()
        diff_dict = diff.diff

        if old_timeline_context is None:
            return None

        if old_timeline_context.id != new_timeline_context.id:
            return None

        if old_timeline_context.name != new_timeline_context.name:
            diff_dict.setdefault("changed", {})
            diff_dict["changed"]["name"] = Diff(old=old_timeline_context.name, new=new_timeline_context.name)

        old_to_new_tracks = cls.map_old_to_new_tracks(old_timeline_context, new_timeline_context)

        for old_index, new_index in old_to_new_tracks.items():
            if new_index is None:
                diff_dict.setdefault("removed", {}).setdefault("video_tracks", {}).setdefault("root", [])
                diff_dict["removed"]["video_tracks"]["root"].append(old_index)
                continue

            if old_index != new_index:
                diff_dict.setdefault("changed", {}).setdefault("video_tracks", {}).setdefault(old_index, {})
                diff_dict["changed"]["video_tracks"][old_index]["index"] = Diff(old=old_index, new=new_index)

            old_track_context = old_timeline_context.video_tracks[old_index]
            new_track_context = new_timeline_context.video_tracks[new_index]

            if old_track_context.name != new_track_context.name:
                diff_dict.setdefault("changed", {}).setdefault("video_tracks", {}).setdefault(old_index, {})
                diff_dict["changed"]["video_tracks"][old_index]["name"] = Diff(old=old_track_context.name, new=new_track_context.name)

            old_item_ids = set(old_track_context.items.keys())
            new_item_ids = set(new_track_context.items.keys())

            for item_id in new_item_ids - old_item_ids:
                diff_dict.setdefault("added", {}).setdefault("video_tracks", {}).setdefault(old_index, {}).setdefault("items", {}).setdefault("root", set())
                diff_dict["added"]["video_tracks"][old_index]["items"]["root"].add(item_id)

            for item_id in old_item_ids - new_item_ids:
                diff_dict.setdefault("removed", {}).setdefault("video_tracks", {}).setdefault(old_index, {}).setdefault("items", {}).setdefault("root", set())
                diff_dict["removed"]["video_tracks"][old_index]["items"]["root"].add(item_id)

        # should track indices be sorted list?
        for new_index in sorted(set(new_timeline_context.video_tracks.keys()) - set(old_to_new_tracks.values())):
            diff_dict.setdefault("added", {}).setdefault("video_tracks", {}).setdefault("root", [])
            diff_dict["added"]["video_tracks"]["root"].append(new_index)

        return diff

    @classmethod
    def map_old_to_new_tracks(cls, old_timeline_context: TimelineContext, new_timeline_context: TimelineContext):
        old_track_items = {track_context.index: set(track_context.items.keys()) for track_context in old_timeline_context.video_tracks.values()}
        new_track_items = {track_context.index: set(track_context.items.keys()) for track_context in new_timeline_context.video_tracks.values()}

        old_to_new_tracks = {}
        moved_tracks = {}

        # check unmoved tracks
        for old_track_index, old_item_ids in old_track_items.copy().items():  # copy to avoid changed size during iteration
            new_item_ids = new_track_items.get(old_track_index)

            if new_item_ids is None:
                continue

            same_items = old_item_ids & new_item_ids

            if len(same_items) > 0:
                old_to_new_tracks[old_track_index] = old_track_index
                old_track_items.pop(old_track_index)
                new_track_items.pop(old_track_index)

        # check moved tracks
        for old_track_index, old_item_ids in old_track_items.copy().items():
            for new_track_index, new_item_ids in new_track_items.copy().items():
                same_items = old_item_ids & new_item_ids

                if len(same_items) > 0:
                    old_to_new_tracks[old_track_index] = new_track_index
                    moved_tracks[old_track_index] = new_track_index
                    old_track_items.pop(old_track_index)
                    new_track_items.pop(new_track_index)
                    break

        # check unmoved empty tracks
        for old_track_index, old_item_ids in old_track_items.copy().items():
            new_item_ids = new_track_items.get(old_track_index)

            if new_item_ids is None:
                continue

            if len(old_item_ids) == 0 or len(new_item_ids) == 0:
                old_to_new_tracks[old_track_index] = old_track_index
                old_track_items.pop(old_track_index)
                new_track_items.pop(old_track_index)

        # lost tracks
        # TODO improve detection of empty tracks?
        old_to_new_tracks.update({i: None for i in old_track_items.keys()})

        return {i: old_to_new_tracks[i] for i in sorted(old_to_new_tracks)}

    def get_new_track_index(self, old_track_index):
        if old_track_index in self.diff.get("removed", {}).get("video_tracks", {}).get("root", []):
            return None

        index_diff = self.diff.get("changed", {}).get("video_tracks", {}).get(old_track_index, {}).get("index")

        if index_diff is None:
            return old_track_index
        else:
            return index_diff.new
