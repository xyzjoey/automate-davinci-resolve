from enum import Enum
from importlib.resources import files

from ..extended_resolve import davinci_resolve_module
from ..extended_resolve.folder import Folder
from ..extended_resolve.media_pool import MediaPool


class SmartEditBin:
    BIN_PATH = files("dvr_smart_edit.data").joinpath("bins/smart_edit.drb")
    FOLDER_NAME = "SmartEdit"

    class ClipPath(Enum):
        TEXTPLUS = "private/Text+"
        EFFECT_CONTROL = "EffectControl"

    @classmethod
    def import_bin(cls):
        media_pool = davinci_resolve_module.get_resolve().get_media_pool()
        cls._get_or_import_bin(media_pool)

    @classmethod
    def get_or_import_textplus(cls):
        return cls._get_or_import_clip(cls.ClipPath.TEXTPLUS)

    @classmethod
    def get_or_import_effect_control(cls):
        return cls._get_or_import_clip(cls.ClipPath.EFFECT_CONTROL)

    @classmethod
    def _get_or_import_clip(cls, clip_path: ClipPath):
        media_pool = davinci_resolve_module.get_resolve().get_media_pool()
        folder = cls._get_or_import_bin(media_pool)

        return cls._find_clip(folder, clip_path)

    @classmethod
    def _find_clip(cls, smart_edit_folder: Folder, clip_path: ClipPath):
        path_tokens = clip_path.value.split("/")

        curr_folder = smart_edit_folder

        for subfolder_name in path_tokens[:-1]:
            curr_folder = curr_folder.find_subfolder(subfolder_name)

            if curr_folder is None:
                return None

        return curr_folder.find_item(lambda item: item.get_clip_name() == path_tokens[-1])

    @classmethod
    def _find_smart_edit_folder(cls, media_pool: MediaPool):
        return media_pool.find_folder(lambda folder: folder.folder_path.depth == 2 and folder._folder.GetName() == cls.FOLDER_NAME)

    @classmethod
    def _get_or_import_bin(cls, media_pool: MediaPool):
        folder = cls._find_smart_edit_folder(media_pool)

        if folder is None:
            media_pool.import_bin(cls.BIN_PATH, media_pool.get_root_folder())
            return cls._find_smart_edit_folder(media_pool)

        missing_clip_paths = [clip_path for clip_path in cls.ClipPath if cls._find_clip(folder, clip_path) is None]

        if len(missing_clip_paths) > 0:
            tmp_folder = Folder(media_pool._media_pool.AddSubFolder(folder._folder, "Temp"))
            media_pool.import_bin(cls.BIN_PATH, tmp_folder)
            tmp_smart_edit_folder = Folder(tmp_folder._folder.GetSubFolderList()[0])

            items = [cls._find_clip(tmp_smart_edit_folder, clip_path) for clip_path in missing_clip_paths]
            media_pool.move_items(items, folder)
            media_pool._media_pool.DeleteFolders([tmp_folder._folder])

        return folder
