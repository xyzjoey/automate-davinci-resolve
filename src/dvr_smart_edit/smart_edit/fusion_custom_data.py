from ..extended_resolve import davinci_resolve_module
from .effect_defines import DEFAULT_EFFECT_TRACKS_SETTINGS, EffectTracksSettings


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

    @staticmethod
    def set_effect_tracks_settings(settings: EffectTracksSettings | None):
        fusion = davinci_resolve_module.get_fusion()

        if settings is not None:
            data = settings.as_dict()
            fusion.SetData("SmartEdit.EffectTracksSettings", data)
        else:
            fusion.SetData("SmartEdit.EffectTracksSettings", None)

    @staticmethod
    def get_effect_tracks_settings():
        fusion = davinci_resolve_module.get_fusion()
        data = fusion.GetData("SmartEdit.EffectTracksSettings")

        if data is None:
            return DEFAULT_EFFECT_TRACKS_SETTINGS

        return EffectTracksSettings.from_lua_like_table(data)
