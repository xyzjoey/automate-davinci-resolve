from typing import Generator, Iterable

from ..extended_resolve.media_pool_item import MediaPoolItem
from ..resolve_types import PyRemoteFolder
from .folder import Folder, FolderPath


class MediaPool:
    def __init__(self, media_pool):
        self._media_pool = media_pool

    def get_root_folder(self):
        return Folder(self._media_pool.GetRootFolder())

    def import_bin(self, file_path, parent_folder: Folder):
        self._media_pool.SetCurrentFolder(parent_folder._folder)
        return self._media_pool.ImportFolderFromFile(str(file_path))

    def get_root_folder(self):
        return Folder(folder_path=FolderPath([self._media_pool.GetRootFolder()]))

    def __iter_folders(self, current_folder: Folder):
        yield current_folder

        for subfolder in current_folder.iter_subfolders():
            yield from self.__iter_folders(subfolder)

    def iter_folders(self) -> Generator[Folder, None, None]:
        yield from self.__iter_folders(self.get_root_folder())

    def find_folder(self, condition) -> Folder | None:
        return next((folder for folder in self.iter_folders() if condition(folder)), None)

    def iter_items(self):
        for folder in self.iter_folders():
            yield from folder.iter_items()

    def find_selected_item(self, condition):
        media_pool_items = self._media_pool.GetSelectedClips()

        if media_pool_items is None:
            return None

        for _item in media_pool_items:
            item = MediaPoolItem(_item)

            if condition(item):
                return item

        return None

    def move_items(self, items: Iterable[MediaPoolItem], target_folder: Folder):
        self._media_pool.MoveClips([item._item for item in items], target_folder._folder)
