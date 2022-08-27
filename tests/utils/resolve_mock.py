class ResolveMockBase:
    def __init__(self, data: dict):
        self._data = data


class ResolveMediaPoolMock(ResolveMockBase):
    pass


class ResolveMediaStorageMock(ResolveMockBase):
    pass


class ResolveTimelineMock(ResolveMockBase):
    def GetSetting(self, name):
        return self._data["setting"][name]


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
