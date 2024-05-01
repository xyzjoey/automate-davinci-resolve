from contextlib import contextmanager

import DaVinciResolveScript

from .enums import ResolveStatus
from .media_pool import MediaPool
from .timeline import Timeline
from ..utils import log


class ResolveApp:
    resolve = None

    def __init__(self):
        # resolve object
        self.project_manager = None
        self.project = None
        self.media_storage = None
        self.media_pool = None
        self.timeline = None

    def load_script_app(self):
        return DaVinciResolveScript.scriptapp("Resolve")

    def update(self):
        if self.resolve is None or self.resolve.GetProductName is None or self.resolve.GetProductName() is None:
            self.resolve = self.load_script_app()

            if self.resolve is None:
                return ResolveStatus.Unavailable

        self.media_storage = self.resolve.GetMediaStorage()
        self.project_manager = self.resolve.GetProjectManager()
        self.project = self.project_manager.GetCurrentProject()  # FIXME can get current project when project not opened
        self.media_pool = None

        if self.project is None:
            return ResolveStatus.ProjectManagerOpen

        self.media_pool = self.project.GetMediaPool()
        self.timeline = self.project.GetCurrentTimeline()

        if self.timeline is None:
            return ResolveStatus.ProjectOpen
        else:
            return ResolveStatus.TimelineOpen

    def get_current_timeline(self):
        return Timeline(self.project.GetCurrentTimeline())

    def get_media_pool(self):
        return MediaPool(self.media_pool)

    @contextmanager
    def import_temp_project(
        self,
        project_file_path: str,
        project_name: str,
        log_prefix="",  # TODO use logger
    ):
        current_project_name = self.project.GetName()

        log.info(f"{log_prefix}Importing temporary project '{project_name}'...")
        log.flush()

        if not self.project_manager.ImportProject(project_file_path, project_name):
            log.error(f"{log_prefix}Failed to import project '{project_name}' from {project_file_path}")
            yield None

        project = self.project_manager.LoadProject(project_name)

        if project is None:
            log.error(f"{log_prefix}Failed to load project '{project_name}'")
            yield None

        self.update()

        yield project

        log.info(f"{log_prefix}Loading back previous project '{current_project_name}'...")
        log.flush()

        if self.project_manager.LoadProject(current_project_name) is None:
            log.error(f"{log_prefix}Failed to load project '{current_project_name}'")

        if not self.project_manager.DeleteProject(project_name):
            log.error(f"{log_prefix}Failed to delete temp project '{project_name}'")

        log.info(f"{log_prefix}Removed temporary project '{project_name}'")

        self.update()
