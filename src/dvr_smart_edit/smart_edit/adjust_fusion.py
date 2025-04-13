from pprint import pprint
from typing import NamedTuple

import luadata

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


class CopyInfo(NamedTuple):
    src_tool: PyRemoteOperator
    src_input_name: str
    dst_tool_name: str
    dst_input_name: str


class AdjustFusion:
    @classmethod
    def get_copy_infos(cls, composition: PyRemoteComposition, adjust_fusion: PyRemoteOperator):
        copy_infos = []

        input_expressions = adjust_fusion.GetInput("SourceInputs")

        for input_expression in input_expressions.split("\n"):
            input_expression = input_expression.strip()
            tokens = input_expression.split(".", maxsplit=1)

            src_tool_name = None
            src_input_name = None

            if len(tokens) == 1:
                src_input_name = tokens[0]
            else:
                src_tool_name = tokens[0]
                src_input_name = tokens[1]

            src_tool = composition.FindTool(src_tool_name) if src_tool_name is not None else adjust_fusion

            if src_tool is None:
                continue

            copy_infos.append(
                CopyInfo(
                    src_tool=src_tool,
                    src_input_name=src_input_name,
                    dst_tool_name=src_tool_name,
                    dst_input_name=src_input_name,
                )
            )

        return copy_infos

    @classmethod
    def get_input_by_name(cls, composition: PyRemoteComposition, tool: PyRemoteOperator, source_input_name: str):
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
    def _set_control(cls, composition, tool, input):
        control_attrs = []
        control_attrs_text = tool.GetInput("ControlAttrs")

        if control_attrs_text:
            control_attrs = luadata.unserialize(control_attrs_text, encoding="utf-8")

            if len(control_attrs) >= 30:
                return

        attrs = input.GetAttrs()
        attrs = cls._convert_to_fuse_attrs(attrs)
        control_attrs.append(attrs)

        luatable = luadata.serialize(control_attrs, encoding="utf-8")
        tool.SetInput("ControlAttrs", luatable)

    @classmethod
    def _convert_to_fuse_attrs(cls, attrs: dict):
        fuse_attrs = {}

        fuse_attrs["INPS_ID"] = attrs["INPS_ID"]
        fuse_attrs["LINKS_Name"] = attrs["INPS_Name"]
        fuse_attrs["LINKID_DataType"] = attrs["INPS_DataType"]
        fuse_attrs["INPID_InputControl"] = attrs["INPID_InputControl"]

        if attrs["INPN_ICD_Width"] > 0:
            fuse_attrs["ICD_Width"] = attrs["INPN_ICD_Width"]

        # in fuse
        # fuse_attrs["IC_Visible"] = True
        # fuse_attrs["INP_External"] = True
        # fuse_attrs["INP_Passive"] = False
        # fuse_attrs["INP_InteractivePassive"] = True

        if fuse_attrs["LINKID_DataType"] == "Number":
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

    @classmethod
    def _set_control_value(cls, composition, tool, input):
        pass

    @classmethod
    def add_control(cls, composition: PyRemoteComposition, add_control_tool: PyRemotePlainInput):
        expression = add_control_tool.AddControl.GetExpression()

        if expression is not None:
            src_input_name = expression.strip()
            src_tool, src_input = cls.get_input_by_name(composition, add_control_tool, src_input_name)

            if src_tool is not None and src_input is not None:
                print(src_tool.GetAttrs())

                cls._set_control(composition, add_control_tool, src_input)

                # source_input_names = add_control_tool.GetInput("SourceInputs")

                # if source_input_names == "":
                #     source_input_names = source_input_name
                # elif source_input_name not in source_input_names:
                #     source_input_names += f"\n{source_input_name}"

                # add_control_tool.SetInput("SourceInputs", source_input_names)

        add_control_tool.AddControl.SetExpression("")

    @classmethod
    def on_copy_for_clip(cls, _adjust_fusion_item: PyRemoteTimelineItem):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()
        adjust_fusion_item = TimelineItem(_adjust_fusion_item)
        comp = adjust_fusion_item.get_last_fusion_composition()
        curr_track_handle = adjust_fusion_item.get_track_handle()
        curr_frame_range = adjust_fusion_item.get_frame_range()

        adjust_fusion = comp.FindToolByID("Fuse.AdjustFusion")
        track_num = adjust_fusion.GetInput("NumberOfTracks")
        # target_inputs = [get_input_from_expression(input_expression) for input_expression in adjust_fusion.GetInput("SourceInputs").split("\n")]
        copy_infos = cls.get_copy_infos(comp, adjust_fusion)

        min_underneath_track_index = max(curr_track_handle.index - track_num, 1)
        max_underneath_track_index = max(curr_track_handle.index - 1, 1)

        if min_underneath_track_index == max_underneath_track_index:
            return

        adjust_fusion_item.get_frame_range()

        for track_index in range(min_underneath_track_index, max_underneath_track_index + 1):
            for item in timeline.iter_items_in_track(
                TrackHandle(curr_track_handle.type, track_index), lambda item: FrameRange.is_started_in_range(item.get_frame_range(), curr_frame_range)
            ):
                dst_comp = item.get_last_fusion_composition()

                if dst_comp is None:
                    continue

                for copy_info in copy_infos:
                    dst_tool = dst_comp.FindTool(copy_info.dst_tool_name)

                    if dst_tool is None:
                        continue

                    value = copy_info.src_tool.GetInput(copy_info.src_input_name)
                    dst_tool.SetInput(copy_info.dst_input_name, value)
