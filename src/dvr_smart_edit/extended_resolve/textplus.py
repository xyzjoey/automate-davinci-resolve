from .fusion_composition import FusionComposition, FusionSettings


class TextPlusToolSettings:
    def __init__(self, _settings: dict):
        self._settings = _settings

    def get_text_value(self):
        return self._settings["Inputs"].get("StyledText", {}).get("Value", "")

    def set_text_value(self, value: str):
        self._settings["Inputs"].setdefault("StyledText", {})
        self._settings["Inputs"]["StyledText"]["Value"] = value


class CharacterLevelStylingToolSettings:
    def __init__(self, _settings: dict):
        self._settings = _settings

    def get_text_value(self):
        return self._settings["Inputs"]["Text"]["Value"]

    def set_text_value(self, value: str):
        self._settings["Inputs"]["Text"]["Value"] = value

    def get_style_array(self):
        return self._settings["Inputs"]["CharacterLevelStyling"]["Value"]["Array"]

    def set_style_array(self, value):
        self._settings["Inputs"]["CharacterLevelStyling"]["Value"]["Array"] = value


class TextPlusCompositionSettings(FusionSettings):
    def get_textplus_tool(self):
        template_tool_settings = self._settings["Tools"].get("Template")

        if template_tool_settings is not None and template_tool_settings["__ctor"] == "TextPlus":
            return TextPlusToolSettings(template_tool_settings)

        tool_settings = next((tool for tool in self._settings["Tools"].values() if tool["__ctor"] == "TextPlus"))
        return TextPlusToolSettings(tool_settings)

    def find_character_level_styling(self, from_textplus_tool_settings: TextPlusToolSettings = None):
        if from_textplus_tool_settings is None:
            from_textplus_tool_settings = self.get_textplus_tool()

        src_operator_name = from_textplus_tool_settings._settings["Inputs"].get("StyledText", {}).get("SourceOp")

        if src_operator_name is None:
            return None

        src_operator_settings = self._settings["Tools"].get(src_operator_name)

        if src_operator_settings is None:
            return None

        if src_operator_settings["__ctor"] == "StyledTextCLS":
            return CharacterLevelStylingToolSettings(src_operator_settings)

        return None

    def get_text_value(self) -> str:
        textplus_tool_settings = self.get_textplus_tool()
        character_level_styling_settings = self.find_character_level_styling(textplus_tool_settings)

        if character_level_styling_settings is not None:
            return character_level_styling_settings.get_text_value()
        else:
            return textplus_tool_settings.get_text_value()

    def set_text_value(self, value: str):
        textplus_tool_settings = self.get_textplus_tool()
        character_level_styling_settings = self.find_character_level_styling(textplus_tool_settings)

        if character_level_styling_settings is not None:
            character_level_styling_settings.set_text_value(value)
        else:
            textplus_tool_settings.set_text_value(value)


class TextPlusComposition(FusionComposition):
    def get_settings(self, tools=None):
        settings = super().get_settings(tools)
        return TextPlusCompositionSettings(settings._settings)
