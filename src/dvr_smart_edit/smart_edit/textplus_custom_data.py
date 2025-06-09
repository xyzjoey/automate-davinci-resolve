from ..resolve_types import PyRemoteComposition, PyRemoteOperator
from .constants import CharacterLevelStylingCopyMode


class TextPlusCustomData:
    @staticmethod
    def set_fit_to_textbox_enabled(textplus_tool: PyRemoteOperator, enabled: bool):
        textplus_tool.SetData("SmartEdit.FitToTextBox", enabled)

    @staticmethod
    def get_fit_to_textbox_enabled(textplus_tool: PyRemoteOperator):
        enabled = textplus_tool.GetData("SmartEdit.FitToTextBox")

        if enabled is None:
            return False

        return enabled

    @staticmethod
    def set_character_styling_level_copy_mode(textplus_composition: PyRemoteComposition, mode: CharacterLevelStylingCopyMode):
        textplus_composition.SetData("SmartEdit.CharacterLevelStylingCopyMode", mode.value)

    @staticmethod
    def get_character_styling_level_copy_mode(textplus_composition: PyRemoteComposition):
        mode_int = textplus_composition.GetData("SmartEdit.CharacterLevelStylingCopyMode")

        if mode_int is None:
            return CharacterLevelStylingCopyMode.NONE

        return CharacterLevelStylingCopyMode(mode_int)
