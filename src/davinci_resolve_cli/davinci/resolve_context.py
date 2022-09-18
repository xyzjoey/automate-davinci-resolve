from enum import Enum

import DaVinciResolveScript

from .media_pool_context import MediaPoolContext
from .timeline_context import TimelineContext


class ResolveStatus(Enum):
    NotAvail = 0
    ProjectManagerAvail = 1
    ProjectAvail = 2
    TimelineAvail = 3


class ResolveContext:
    instance = None

    def __init__(self):
        # resolve object
        self.resolve = None
        self.project_manager = None
        self.project = None
        self.media_storage = None
        self.media_pool = None

        self.update()

    @classmethod
    def get(cls) -> "ResolveContext":
        if cls.instance is None:
            cls.instance = ResolveContext()
        return cls.instance

    def update(self):
        if self.resolve is None or self.resolve.GetProductName is None or self.resolve.GetProductName() is None:
            self.resolve = DaVinciResolveScript.scriptapp("Resolve")

            if self.resolve is None:
                return ResolveStatus.NotAvail

        self.media_storage = self.resolve.GetMediaStorage()
        self.project_manager = self.resolve.GetProjectManager()
        self.project = self.project_manager.GetCurrentProject()
        self.media_pool = None

        if self.project is None:
            return ResolveStatus.ProjectManagerAvail

        self.media_pool = self.project.GetMediaPool()

        if self.project.GetCurrentTimeline() is None:
            return ResolveStatus.ProjectAvail
        else:
            return ResolveStatus.TimelineAvail

    def print_timeline_item(self, timeline_item):
        print(f"\tClip Name: {timeline_item.GetName()}")

    def add_folder_if_not_exist(self, folder, name):
        subfolders = folder.GetSubFolderList()
        subfolder_with_same_name = next((subfolder for subfolder in subfolders if subfolder.GetName() == name), None)

        if subfolder_with_same_name is not None:
            return subfolder_with_same_name
        else:
            new_folder = self.media_pool.AddSubFolder(folder, name)
            return new_folder

    def get_current_timeline_context(self):
        return TimelineContext(self.project.GetCurrentTimeline())

    def get_media_pool_context(self):
        return MediaPoolContext(self.media_pool)
