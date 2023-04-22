from automate_davinci_resolve.davinci.resolve_app import ResolveApp
from automate_davinci_resolve.davinci.timecode import Timecode, TimecodeSettings
from automate_davinci_resolve.davinci.timeline import Timeline


class ResolveMockBase:
    def __init__(self, data: dict):
        self._data = data


class ResolveMediaPoolMock(ResolveMockBase):
    pass


class ResolveMediaStorageMock(ResolveMockBase):
    pass


class ResolveFusionNodeInputMock(ResolveMockBase):
    def GetAttrs(self, name: str):
        return self._data.get(name)

    def GetExpression(self):
        return self._data.get("expression")

    def SetExpression(self, expression):
        self._data["expression"] = expression


class ResolveFusionNodeMock(ResolveMockBase):
    def GetInput(self, name: str):
        return self._data.get(name)

    def GetInputList(self):
        return {key: ResolveFusionNodeInputMock({"INPS_ID": key}) for key in self._data}

    def SetInput(self, name: str, value):
        self._data[name] = value


class ResolveFusionCompMock(ResolveMockBase):
    def FindToolByID(self, id: str):
        node = self._data.get(id, None)

        return ResolveFusionNodeMock(node) if node is not None else None


class ResolveTimelineItemMock(ResolveMockBase):
    def __init__(self, data: dict, timecode_settings: TimecodeSettings):
        super().__init__(data)
        self.timecode_settings = timecode_settings

    def GetUniqueId(self) -> str:
        return self._data.get("id")

    def GetName(self) -> str:
        return self._data.get("name")

    def GetStart(self) -> int:
        return Timecode.from_str(self._data["start"], self.timecode_settings, True).get_frame(True)

    def GetEnd(self) -> int:
        return Timecode.from_str(self._data["end"], self.timecode_settings, True).get_frame(True)

    def GetFusionCompCount(self) -> int:
        return len(self._data.get("fusion_comps", {}))

    def GetFusionCompByIndex(self, index: int):
        comp = self._data.get("fusion_comps", {}).get(index, None)

        return ResolveFusionCompMock(comp) if comp is not None else None

    def GetClipColor(self) -> str:
        return self._data.get("clip_color", "")


class ResolveTimelineMock(ResolveMockBase):
    def GetUniqueId(self):
        return self._data.get("id")

    def GetName(self) -> str:
        return self._data.get("name")

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

        timecode_settings = Timeline(self).get_timecode_settings()

        return [ResolveTimelineItemMock(item, timecode_settings) for item in items] if items is not None else None


class ResolveProjectMock(ResolveMockBase):
    def GetMediaPool(self):
        return ResolveMediaPoolMock(self._data["media_pool"])

    def GetCurrentTimeline(self):
        return ResolveTimelineMock(self._data.get("current_timeline"))

    def GetSetting(self, name):
        return self._data["setting"][name]


class ResolveProjectManagerMock(ResolveMockBase):
    def GetCurrentProject(self):
        return ResolveProjectMock(self._data["current_project"])


class ResolveScriptAppMock(ResolveMockBase):
    def GetProductName(self):
        return self._data.get("product_name")

    def GetProjectManager(self):
        return ResolveProjectManagerMock(self._data["project_manager"])

    def GetMediaStorage(self):
        return ResolveMediaStorageMock(self._data["media_storage"])


class ResolveAppMock(ResolveApp):
    def __init__(self):
        super().__init__()

        self.mock_data = None

    def load_script_app(self):
        if self.mock_data is None:
            return None

        return ResolveScriptAppMock(self.mock_data)

    def mock_current_project(self, data):
        if self.mock_data is None:
            self.mock_data = {
                "product_name": "resolve",
                "project_manager": {
                    "current_project": {
                        "media_pool": {},
                    }
                },
                "media_storage": {},
            }

        self.mock_data["project_manager"]["current_project"].update(data)
        self.update()

    def mock_current_timeline(self, data):
        if self.mock_data is None:
            self.mock_data = {
                "product_name": "resolve",
                "project_manager": {
                    "current_project": {
                        "media_pool": {},
                        "current_timeline": {
                            "setting": {"timelineFrameRate": 60.0},
                            "start_timecode": "01:00:00:00",
                        },
                    }
                },
                "media_storage": {},
            }

        self.mock_data["project_manager"]["current_project"]["current_timeline"].update(data)
        self.update()

    def get_mocked_current_timeline(self):
        return self.mock_data.get("project_manager", {}).get("current_project", {}).get("current_timeline", None)
