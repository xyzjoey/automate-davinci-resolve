from enum import Enum

import DaVinciResolveScript

from .timeline_context import TimelineContext


class ResolveStatus(Enum):
    NotAvail = 0
    ProjectAvail = 1
    TimelineAvail = 2


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

        self.project_manager = self.resolve.GetProjectManager()
        self.project = self.project_manager.GetCurrentProject()
        self.media_storage = self.resolve.GetMediaStorage()
        self.media_pool = self.project.GetMediaPool()

        if self.project.GetCurrentTimeline() is None:
            return ResolveStatus.ProjectAvail
        else:
            return ResolveStatus.TimelineAvail

    def print_timeline_item(self, timeline_item):
        print(f"\tClip Name: {timeline_item.GetName()}")

    def get_unique_timeline_name(self, name) -> str:
        timeline_names = [self.project.GetTimelineByIndex(i + 1).GetName() for i in range(self.project.GetTimelineCount())]

        new_name = name
        index = 0

        while new_name in timeline_names:
            index += 1
            new_name = f"{name} {index}"

        return new_name

    def create_timeline(self, desired_name):
        actual_name = self.get_unique_timeline_name(desired_name)

        timeline = self.media_pool.CreateEmptyTimeline(actual_name)

        assert timeline is not None, "Failed to create timeline"
        assert self.project.SetCurrentTimeline(timeline), "Failed to set current timeline (timeline={timeline})"

        return actual_name, timeline

    def iter_media_pool_items(self):
        folder_stacks = [[self.media_pool.GetRootFolder()]]

        while folder_stacks != [[]]:
            current_path = [folders[0] for folders in folder_stacks]
            current_folder = folder_stacks[-1][0]

            for media_pool_item in current_folder.GetClipList():
                yield media_pool_item, current_path

            subfolders = list(current_folder.GetSubFolderList())

            if len(subfolders) > 0:
                folder_stacks.append(subfolders)
            else:
                folder_stacks[-1].pop(0)

                while len(folder_stacks[-1]) == 0 and len(folder_stacks) > 1:
                    folder_stacks.pop()
                    folder_stacks[-1].pop(0)

    def get_media_pool_item(self, path: str):
        tokens = path.split("/")
        folder_names = tokens[:-1]
        clip_name = tokens[-1]

        current_folder = self.media_pool.GetRootFolder() if path.startswith("/") else self.media_pool.GetCurrentFolder()

        for folder_name in folder_names:
            if folder_name == "":
                continue

            subfolder = next((f for f in current_folder.GetSubFolderList() if f.GetName() == folder_name), None)

            if subfolder is None:
                raise Exception(f"Folder '{folder_name}' does not exist under '{current_folder.GetName()}'")

            current_folder = subfolder

        clip = next((clip for clip in current_folder.GetClipList() if clip.GetClipProperty("Clip Name") == clip_name), None)

        if clip is None:
            raise Exception(f"Clip '{clip_name}' does not exist under folder '{current_folder.GetName()}'")

        return clip

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
