# from ..extended_resolve import davinci_resolve_module
# from ..extended_resolve.constants import MediaPoolItemType
# from ..extended_resolve.media_pool_item import MediaPoolItem
# from ..extended_resolve.track import TrackHandle
from ..resolve_types import PyRemoteComposition
from ..smart_edit.adjust_fusion import AdjustFusion
from ..smart_edit.errors import UserError
from ..smart_edit.ui.loading_window import LoadingWindow
from .script_utils import ScriptUtils


def on_add_control(composition: PyRemoteComposition, fuse_name: str):
    _, comp, tool = ScriptUtils.find_fuse_in_timeline(composition, fuse_name)

    if tool is not None:
        AdjustFusion.add_control(comp, tool)


def on_set_control_value(composition: PyRemoteComposition, fuse_name: str):
    _, comp, tool = ScriptUtils.find_fuse_in_timeline(composition, fuse_name)

    if tool is not None:
        AdjustFusion.set_control_value(comp, tool)


def on_apply_for_clip(composition: PyRemoteComposition):
    with LoadingWindow("Adjust Fusion", "Applying..."):
        item, _ = ScriptUtils.find_composition_in_timeline(composition)

        if item is None:
            raise UserError("Cannot find clip in timeline")

        AdjustFusion.apply_for_clip(item)
