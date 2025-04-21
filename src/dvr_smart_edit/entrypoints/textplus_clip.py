from pathlib import Path

from ..extended_resolve import davinci_resolve_module
from ..extended_resolve.constants import MediaPoolItemType
from ..extended_resolve.media_pool_item import MediaPoolItem
from ..resolve_types import PyRemoteComposition, PyRemoteOperator
from ..smart_edit.errors import UserError
from ..smart_edit.textplus_utilities import TextplusLinkTool, TextPlusUtilities
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
        timeline_item, _ = ScriptUtils.find_composition_in_timeline(composition)

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
        timeline_item, _ = ScriptUtils.find_composition_in_timeline(composition)

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
        timeline_item, _ = ScriptUtils.find_composition_in_timeline(composition)

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


def on_enable_fit_to_textbox(textplus_tool: PyRemoteOperator):
    with ErrorWindow.pop_on_error():
        TextplusLinkTool.enable_fit_to_textbox(textplus_tool)


def on_disable_fit_to_textbox(textplus_tool: PyRemoteOperator):
    with ErrorWindow.pop_on_error():
        TextplusLinkTool.disable_fit_to_textbox(textplus_tool)
