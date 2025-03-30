# from ..extended_resolve import davinci_resolve_module
# from ..extended_resolve.constants import MediaPoolItemType
# from ..extended_resolve.media_pool_item import MediaPoolItem
# from ..extended_resolve.track import TrackHandle
from ..resolve_types import PyRemoteComposition
from ..smart_edit.adjust_fusion import AdjustFusion
from ..smart_edit.ui.loading_window import LoadingWindow
from .script_utils import ScriptUtils


def on_add_control(composition: PyRemoteComposition, tool_name: str):
    if composition is None:
        return

    tool = composition.FindTool(tool_name)

    if tool is not None:
        AdjustFusion.add_control(composition, tool)


# def on_set_control_value(composition: PyRemoteComposition, tool_name: str):
#     if composition is None:
#         return

#     tool = composition.FindTool(tool_name)

#     if tool is not None:
#         AdjustFusion.set_control(composition, tool)


def on_copy_for_clip(composition: PyRemoteComposition):
    with LoadingWindow("Adjust Fusion", "Copying..."):
        curr_item = ScriptUtils.get_timeline_item_from_composition(composition)

        AdjustFusion.copy_for_clip(curr_item)
