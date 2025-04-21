from ..extended_resolve import davinci_resolve_module


class FusionCustomData:
    @staticmethod
    def set_init_fusion_enabled(enabled: bool):
        fusion = davinci_resolve_module.get_fusion()
        fusion.SetData("SmartEdit.InitFusionEnabled", enabled)

    @staticmethod
    def get_init_fusion_enabled():
        fusion = davinci_resolve_module.get_fusion()
        enabled = fusion.GetData("SmartEdit.InitFusionEnabled")

        if enabled is None:
            return True

        return enabled
