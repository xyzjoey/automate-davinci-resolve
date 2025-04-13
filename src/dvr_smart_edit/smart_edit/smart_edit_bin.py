from enum import Enum
from importlib.resources import files

from ..extended_resolve import davinci_resolve_module
from ..extended_resolve.folder import Folder
from ..extended_resolve.media_pool import MediaPool


class SmartEditBin:
    BIN_PATH = files("dvr_smart_edit.data").joinpath("bins/smart_edit.drb")
    FOLDER_NAME = "SmartEdit"

    class ClipName(Enum):
        TEXTPLUS = "Text+"
        EFFECT_CONTROL = "EffectControl"

    @classmethod
    def import_bin(cls):
        media_pool = davinci_resolve_module.get_resolve().get_media_pool()
        cls._get_or_import_bin(media_pool)

    @classmethod
    def get_or_import_textplus(cls):
        return cls._get_or_import_clip(cls.ClipName.TEXTPLUS)

    @classmethod
    def get_or_import_effect_control(cls):
        return cls._get_or_import_clip(cls.ClipName.EFFECT_CONTROL)

    @classmethod
    def _get_or_import_clip(cls, clip_name: ClipName):
        media_pool = davinci_resolve_module.get_resolve().get_media_pool()
        folder = cls._get_or_import_bin(media_pool)

        return folder.find_item(lambda item: item.get_clip_name() == clip_name.value)

    @classmethod
    def _find_smart_edit_folder(cls, media_pool: MediaPool):
        return media_pool.find_folder(lambda folder: folder.folder_path.depth == 2 and folder._folder.GetName() == cls.FOLDER_NAME)

    @classmethod
    def _get_or_import_bin(cls, media_pool: MediaPool):
        folder = cls._find_smart_edit_folder(media_pool)

        if folder is None:
            media_pool.import_bin(cls.BIN_PATH, media_pool.get_root_folder())
            return cls._find_smart_edit_folder(media_pool)

        item_names = [item.get_clip_name() for item in folder.iter_items()]
        missing_clip_names = [clip_name.value for clip_name in cls.ClipName if clip_name.value not in item_names]

        if len(missing_clip_names) > 0:
            tmp_folder = Folder(media_pool._media_pool.AddSubFolder(folder._folder, "Temp"))
            media_pool.import_bin(cls.BIN_PATH, tmp_folder)
            tmp_smart_edit_folder = Folder(tmp_folder._folder.GetSubFolderList()[0])

            items = tmp_smart_edit_folder.find_items(lambda item: item.get_clip_name() in missing_clip_names)
            media_pool.move_items(items, folder)
            media_pool._media_pool.DeleteFolders([tmp_folder._folder])

        return folder
