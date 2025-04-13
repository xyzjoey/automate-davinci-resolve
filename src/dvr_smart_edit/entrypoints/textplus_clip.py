import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from ..extended_resolve import davinci_resolve_module
from ..extended_resolve.constants import MediaPoolItemType
from ..extended_resolve.media_pool_item import MediaPoolItem
from ..resolve_types import PyRemoteComposition
from ..smart_edit.errors import UserError
from ..smart_edit.textplus_utilities import TextPlusUtilities
from ..smart_edit.ui.error_window import ErrorWindow
from ..smart_edit.ui.loading_window import LoadingWindow
from .script_utils import ScriptUtils


def _is_textplus_item(item: MediaPoolItem):
    return item.get_clip_type() == MediaPoolItemType.FUSION_TITLE


def on_copy_style_for_all():  # TODO: preserve style on regeneration
    with LoadingWindow("SmartEdit Text+", "Copying Style..."):
        resolve = davinci_resolve_module.get_resolve()
        media_pool = resolve.get_media_pool()
        media_pool_item = media_pool.find_selected_item(_is_textplus_item)

        if media_pool_item is None:
            raise UserError("No Media Pool Text+ clip selected")

        TextPlusUtilities.copy_style_for_all(media_pool_item)


def on_copy_style_for_track(composition: PyRemoteComposition):
    with LoadingWindow("SmartEdit Text+", "Copying Style..."):
        timeline_item, _ = ScriptUtils.get_timeline_item_from_composition(composition)

        if timeline_item is None:
            raise UserError("Fusion in Effects Tab or Subtitle Track is not supported")

        resolve = davinci_resolve_module.get_resolve()
        media_pool = resolve.get_media_pool()
        media_pool_item = media_pool.find_selected_item(_is_textplus_item)

        if media_pool_item is None:
            raise UserError("No Media Pool Text+ clip selected")

        TextPlusUtilities.copy_style_for_track(timeline_item.get_track_handle(), media_pool_item)


def on_copy_style_for_clip(composition: PyRemoteComposition):
    with ErrorWindow.pop_on_error():
        timeline_item, _ = ScriptUtils.get_timeline_item_from_composition(composition)

        if timeline_item is None:
            raise UserError("Fusion in Effects Tab or Subtitle Track is not supported")

        resolve = davinci_resolve_module.get_resolve()
        media_pool = resolve.get_media_pool()
        media_pool_item = media_pool.find_selected_item(_is_textplus_item)

        if media_pool_item is None:
            raise UserError("No Media Pool Text+ clip selected")

        TextPlusUtilities.copy_style_for_clip(timeline_item, media_pool_item)


def on_export_srt_for_track(composition: PyRemoteComposition):
    timeline_item = None
    file_path = None

    with ErrorWindow.pop_on_error():
        timeline_item, _ = ScriptUtils.get_timeline_item_from_composition(composition)

        if timeline_item is None:
            raise UserError("Fusion in Effects Tab or Subtitle Track is not supported")

        fusion = davinci_resolve_module.get_fusion()
        file_path = fusion.RequestFile(
            "",
            "",
            {
                "FReqS_Filter": "Subtitle Files (*.srt)|*.srt",
                "FReqS_Tiitle": "Smart Edit - Import Subtitle",
                "FReqB_Saving": True,
            },
        )

        if not file_path:
            return

    if timeline_item is not None and file_path is not None:
        with LoadingWindow("SmartEdit Text+", "Exporting Srt..."):
            TextPlusUtilities.export_srt_for_track(timeline_item.get_track_handle(), Path(file_path))


def on_fit_textbox_for_clip(composition: PyRemoteComposition):
    with ErrorWindow.pop_on_error():
        timeline_item, _ = ScriptUtils.get_timeline_item_from_composition(composition)

        if timeline_item is None:
            raise UserError("Fusion in Effects Tab or Subtitle Track is not supported")

        TextPlusUtilities.fit_textbox_for_clip(timeline_item)


# def on_fit_to_textbox_for_clip(composition: PyRemoteComposition):
#     timeline_item, _ = ScriptUtils.get_timeline_item_from_composition(composition)

#     if timeline_item is None:
#         with LoadingWindow("SmartEdit Text+", "Fit Text Box..."):  # TODO: ErrorWindow
#             raise UserError("Fusion in Effects Tab or Subtitle Track is not supported")

#     UniTextPlusControl.fit_to_textbox_for_clip(composition)


# def on_fit_to_textbox_for_all():
#     with LoadingWindow("SmartEdit Text+", "Fitting all Text+ to Text Box..."):
#         UniTextPlusControl.fit_to_textbox_for_all()


# def on_enable_fit_to_textbox(composition: PyRemoteComposition, fuse_name: str):
#     _, tool = ScriptUtils.get_tool_from_fuse_name(composition, fuse_name)

#     if tool is not None:
#         print("on_enable_fit_to_textbox")
#     #     UniTextPlusControl.enable_fit_to_textbox(tool)


# def on_disable_fit_to_textbox(composition: PyRemoteComposition, fuse_name: str):
#     _, tool = ScriptUtils.get_tool_from_fuse_name(composition, fuse_name)

#     if tool is not None:
#         print("on_disable_fit_to_textbox")
#     #     UniTextPlusControl.disable_fit_to_textbox(tool)


# def on_created(composition: PyRemoteComposition, fuse_name: str):
#     ScriptUtils.find_fuse_in_timeline(composition, fuse_name)
#     # comp, tool = ScriptUtils.get_tool_from_fuse_name(composition, fuse_name)

#     # if tool is not None:
#     #     UniTextPlusControl.init_nodes(comp, tool)
#     # UniTextPlusControl.reset_resolution(composition, tool)


# def on_set_value(composition: PyRemoteComposition, fuse_name: str, input_id: str):
#     comp, tool = ScriptUtils.get_tool_from_fuse_name(composition, fuse_name)

#     if tool is not None:
#         UniTextPlusControl.set_value(comp, tool, input_id)


# def on_debug(obj):
#     print("on_debug!!")
#     # print(dir(obj))
#     # print(obj.Comp())
#     comp = obj.Comp()

#     timeline_item, comp = ScriptUtils.get_timeline_item_from_composition(comp)
#     print(f"timeline_item={timeline_item} {timeline_item.get_track_handle()} {timeline_item.get_frame_range()}")
#     print(f"comp={comp}")
