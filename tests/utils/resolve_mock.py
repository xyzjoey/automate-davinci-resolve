from davinci_resolve_cli.davinci.timecode import TimecodeContext
from davinci_resolve_cli.davinci.timeline_context import TimelineContext


class ResolveMockBase:
    def __init__(self, data: dict):
        self._data = data


class ResolveMediaPoolMock(ResolveMockBase):
    pass


class ResolveMediaStorageMock(ResolveMockBase):
    pass


class ResolveFusionNodeMock(ResolveMockBase):
    def GetInput(self, name: str):
        return self._data.get(name)


class ResolveFusionCompMock(ResolveMockBase):
    def FindToolByID(self, id: str):
        node = self._data.get(id, None)

        return ResolveFusionNodeMock(node) if node is not None else None


class ResolveTimelineItemMock(ResolveMockBase):
    def __init__(self, data: dict, timecode_context: TimecodeContext):
        super().__init__(data)
        self.timecode_context = timecode_context

    def GetStart(self) -> int:
        return self.timecode_context.create_timecode_from_str(self._data["start"], True).get_frame(True)

    def GetEnd(self) -> int:
        return self.timecode_context.create_timecode_from_str(self._data["end"], True).get_frame(True)

    def GetFusionCompCount(self) -> int:
        return len(self._data.get("fusion_comps", {}))

    def GetFusionCompByIndex(self, index: int):
        comp = self._data.get("fusion_comps", {}).get(index, None)

        return ResolveFusionCompMock(comp) if comp is not None else None


class ResolveTimelineMock(ResolveMockBase):
    def GetSetting(self, name) -> float:
        return self._data["setting"][name]

    def GetStartTimecode(self) -> str:
        return self._data["start_timecode"]

    def GetTrackCount(self, track_type: str) -> int:
        return len(self._data.get("tracks", {}).get(track_type, {}))

    def GetTrackName(self, track_type: str, track_index: int) -> str:
        return self._data.get("tracks", {}).get(track_type, {}).get(track_index, {}).get("name", None)

    def GetItemListInTrack(self, track_type: str, track_index: int):
        items = self._data.get("tracks", {}).get(track_type, {}).get(track_index, {}).get("items", None)

        timecode_context = TimelineContext(self).get_timecode_context()

        return [ResolveTimelineItemMock(item, timecode_context) for item in items] if items is not None else None


class ResolveProjectMock(ResolveMockBase):
    def GetMediaPool(self):
        return ResolveMediaPoolMock(self._data["media_pool"])

    def GetCurrentTimeline(self):
        return ResolveTimelineMock(self._data["current_timeline"])


class ResolveProjectManagerMock(ResolveMockBase):
    def GetCurrentProject(self):
        return ResolveProjectMock(self._data["current_project"])


class ResolveAppMock(ResolveMockBase):
    def GetProjectManager(self):
        return ResolveProjectManagerMock(self._data["project_manager"])

    def GetMediaStorage(self):
        return ResolveMediaStorageMock(self._data["media_storage"])


def scriptapp(_):
    pass  # mocked in conftest.py
