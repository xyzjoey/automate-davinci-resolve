from ..extended_resolve import davinci_resolve_module
from ..resolve_types import PyRemoteComposition, PyRemoteOperator, PyRemotePlainInput


class FusionTool:
    @classmethod
    def copy_input_value(cls, src_input, dst_tool, dst_input):
        fusion = davinci_resolve_module.get_fusion()

        keyframes = src_input.GetKeyFrames()

        if not keyframes:
            src_value = src_input[fusion.TIME_UNDEFINED]
            dst_tool.SetInput(dst_input.ID, src_value)
        else:
            out = src_input.GetConnectedOutput()
            spline = out.GetTool()
            setattr(dst_tool, dst_input.ID, spline)
