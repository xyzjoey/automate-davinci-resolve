from pprint import pprint
from typing import Any, NamedTuple

from ..extended_resolve import davinci_resolve_module
from ..extended_resolve.constants import MediaPoolItemType
from ..extended_resolve.media_pool_item import MediaPoolItem
from ..extended_resolve.timeline_item import TimelineItem
from ..extended_resolve.track import TrackHandle
from ..resolve_types import (
    PyRemoteComposition,
    PyRemoteOperator,
    PyRemotePlainInput,
    PyRemoteTimelineItem,
)
from ..smart_edit.errors import UserError
from ..smart_edit.ui.loading_window import LoadingWindow
from ..utils.math import FrameRange


class ControlInfo(NamedTuple):
    dst_tool_name: str
    dst_input_name: str
    value: Any
    animated: bool


class AdjustFusion:
    @classmethod
    def add_control(cls, composition: PyRemoteComposition, fuse_tool: PyRemotePlainInput):
        expression = fuse_tool.AddControl.GetExpression()

        if expression is not None:
            src_input_name = expression.strip()
            src_tool, src_input = cls._get_input_by_name(composition, fuse_tool, src_input_name)

            if src_tool is not None and src_input is not None:
                new_control_index = cls._set_control(fuse_tool, src_tool, src_input)

                if new_control_index is not None:
                    fuse_tool.SetData("SmartEdit.PendingControlIndex", new_control_index)
                    fuse_tool.SetData("SmartEdit.PendingInputName", src_input_name)

        fuse_tool.AddControl.SetExpression("")

    @classmethod
    def set_control_value(cls, composition: PyRemoteComposition, fuse_tool: PyRemotePlainInput):
        fusion = davinci_resolve_module.get_fusion()

        control_index = fuse_tool.GetData("SmartEdit.PendingControlIndex")
        src_input_name = fuse_tool.GetData("SmartEdit.PendingInputName")

        if control_index is None or src_input_name is None:
            return

        control_index = int(control_index)

        src_tool, src_input = cls._get_input_by_name(composition, fuse_tool, src_input_name)

        if src_tool is not None and src_input is not None:
            keyframes = src_input.GetKeyFrames()

            if not keyframes:
                src_value = src_input[fusion.TIME_UNDEFINED]
                fuse_tool.SetInput(f"AdjustControl{control_index + 1}", src_value)
            else:
                out = src_input.GetConnectedOutput()
                spline = out.GetTool()
                setattr(fuse_tool, f"AdjustControl{control_index + 1}", spline)

            use_previous = fuse_tool.GetInput(f"UsePreviousNode{control_index + 1}") and (control_index > 0)

            if use_previous:
                prev_dst_node = fuse_tool.GetInput(f"DestinationNode{control_index}")
                fuse_tool.SetInput(f"DestinationNode{control_index + 1}", prev_dst_node)
            else:
                fuse_tool.SetInput(f"DestinationNode{control_index + 1}", src_tool.Name)

            fuse_tool.SetInput(f"DestinationInputId{control_index + 1}", src_input.GetAttrs("INPS_ID"))

        fuse_tool.SetData("SmartEdit.PendingControlIndex", None)
        fuse_tool.SetData("SmartEdit.PendingInputName", None)

    @classmethod
    def apply_for_clip(cls, adjust_fusion_item: TimelineItem):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()

        src_comp = adjust_fusion_item.get_last_fusion_composition()
        src_tool = src_comp.FindToolByID("Fuse.AdjustFusion")
        src_track_handle = adjust_fusion_item.get_track_handle()
        src_frame_range = adjust_fusion_item.get_frame_range()

        track_num = int(src_tool.GetInput("NumberOfTracks"))
        control_infos = cls._get_control_infos(src_tool)

        track_index_start = max(src_track_handle.index - track_num, 1)
        track_index_end = max(src_track_handle.index - 1, 1)

        if track_index_start == src_track_handle.index:
            return

        for track_index in range(track_index_start, track_index_end + 1):
            for item in timeline.iter_items_in_track(
                TrackHandle(src_track_handle.type, track_index),
                lambda item: FrameRange.is_started_in_range(item.get_frame_range(), src_frame_range),
            ):
                dst_comp = item.get_last_fusion_composition()

                if dst_comp is None:
                    continue

                for control_info in control_infos:
                    dst_tool = dst_comp.FindTool(control_info.dst_tool_name)

                    if dst_tool is None:
                        continue

                    dst_input = getattr(dst_tool, control_info.dst_input_name)

                    if dst_input is None:
                        continue

                    if control_info.animated == False:
                        dst_tool.SetInput(control_info.dst_input_name, control_info.value)
                    else:
                        setattr(dst_tool, control_info.dst_input_name, control_info.value)

    @classmethod
    def _get_control_infos(cls, fuse_tool: PyRemoteOperator) -> list[ControlInfo]:
        fusion = davinci_resolve_module.get_fusion()
        fuse_control_infos = cls._get_fuse_control_infos(fuse_tool)

        control_infos = []

        for i in range(len(fuse_control_infos)):
            value = None
            animated = False

            src_input = getattr(fuse_tool, f"AdjustControl{i + 1}")
            keyframes = src_input.GetKeyFrames()

            if not keyframes:
                value = src_input[fusion.TIME_UNDEFINED]
            else:
                out = src_input.GetConnectedOutput()
                value = out.GetTool()
                animated = True

            control_infos.append(
                ControlInfo(
                    dst_tool_name=fuse_tool.GetInput(f"DestinationNode{i + 1}"),
                    dst_input_name=fuse_tool.GetInput(f"DestinationInputId{i + 1}"),
                    value=value,
                    animated=animated,
                )
            )

        return control_infos

    @classmethod
    def _get_input_by_name(cls, composition: PyRemoteComposition, tool: PyRemoteOperator, source_input_name: str):
        tokens = source_input_name.split(".", maxsplit=1)

        if len(tokens) == 1:
            return None, None

        src_tool_name = tokens[0]
        src_input_name = tokens[1]

        src_tool = composition.FindTool(src_tool_name)

        if src_tool is None:
            return None, None

        src_input = getattr(src_tool, src_input_name)

        return src_tool, src_input

    @classmethod
    def _get_fuse_control_infos(cls, fuse_tool):
        fuse_control_infos = fuse_tool.GetData("SmartEdit.ControlInfos")

        if fuse_control_infos:
            if isinstance(fuse_control_infos, dict):
                return [v for k, v in fuse_control_infos.items() if k != "__flags"]
            else:
                return fuse_control_infos

        return []

    @classmethod
    def _set_control(cls, fuse_tool, src_tool, src_input):
        fuse_control_infos = cls._get_fuse_control_infos(fuse_tool)

        if len(fuse_control_infos) >= 30:
            return None

        input_attrs = src_input.GetAttrs()
        fuse_attrs = cls._convert_to_fuse_attrs(input_attrs)
        control_info = {
            "attrs": fuse_attrs,
            "default_destination_node": src_tool.Name,
            "default_destination_input_id": input_attrs["INPS_ID"],
        }
        fuse_control_infos.append(control_info)

        fuse_tool.SetData("SmartEdit.ControlInfos", fuse_control_infos)
        fuse_tool.SetInput("PendingControl", 1)

        return len(fuse_control_infos) - 1

    @classmethod
    def _convert_to_fuse_attrs(cls, attrs: dict):
        fuse_attrs = {}

        fuse_attrs["LINKS_Name"] = attrs["INPS_Name"]
        fuse_attrs["LINKID_DataType"] = attrs["INPS_DataType"]
        fuse_attrs["INPID_InputControl"] = attrs["INPID_InputControl"]

        if attrs["INPN_ICD_Width"] > 0:
            fuse_attrs["ICD_Width"] = attrs["INPN_ICD_Width"]

        # dynamic default for text and checkbox cause value not being preserved
        if fuse_attrs["LINKID_DataType"] == "Number" and fuse_attrs["INPID_InputControl"] != "CheckboxControl":
            fuse_attrs["INP_Default"] = attrs["INPN_Default"]

        if "INPID_PreviewControl" in attrs:
            fuse_attrs["INPID_PreviewControl"] = attrs["INPID_PreviewControl"]
            fuse_attrs["PC_ControlGroup"] = attrs["INPI_PC_ControlGroup"]
            fuse_attrs["PC_ControlID"] = attrs["INPI_PC_ControlID"]

        # MultiButtonControl
        if "INPST_MultiButtonControl_String" in attrs:
            for i, button_name in attrs["INPST_MultiButtonControl_String"].items():
                fuse_attrs[i] = {"MBTNC_AddButton": button_name}
            # fuse_attrs.MBTNC_ShowName = attrs.INPB_MultiButtonControl_ShowName

        # MultiButtonIDControl
        if "INPIDT_MultiButtonControl_ID" in attrs:
            for i, button_name in attrs["INPIDT_MultiButtonControl_ID"].items():
                fuse_attrs[i] = {"MBTNC_AddButton": button_name}

        return fuse_attrs
