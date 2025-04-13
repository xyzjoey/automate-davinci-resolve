from ..resolve_types import PyRemoteComposition


class InputSettings:
    def __init__(self, _settings: dict):
        self._settings = _settings


class TextPlusToolSettings:
    def __init__(self, _settings: dict):
        self._settings = _settings

    def get_text_input(self):
        return InputSettings(self._settings["Inputs"]["StyledText"])


class CharacterLevelStylingToolSettings:
    def __init__(self, _settings: dict):
        self._settings = _settings

    def get_text_input(self):
        return InputSettings(self._settings["Inputs"]["Text"])

    @property
    def style_array(self):
        return self._settings["Inputs"]["CharacterLevelStyling"]["Value"]["Array"]

    @style_array.setter
    def style_array(self, value):
        self._settings["Inputs"]["CharacterLevelStyling"]["Value"]["Array"] = value


class TextPlusSettings:
    def __init__(self, _settings: dict):
        self._settings = _settings

    def get_tool(self, name):
        return self._settings["Tools"].get(name)

    def get_textplus_tool(self):
        _tool = next((tool for tool in self._settings["Tools"].values() if tool["__ctor"] == "TextPlus"))
        return TextPlusToolSettings(_tool)

    def find_character_level_styling(self):
        _tool = next((tool for tool in self._settings["Tools"].values() if tool["__ctor"] == "StyledTextCLS"), None)
        return CharacterLevelStylingToolSettings(_tool) if _tool is not None else None

    def get_text_input(self):
        textplus_tool = self.get_textplus_tool()
        character_level_styling_tool = self.find_character_level_styling()

        if character_level_styling_tool is not None:
            return character_level_styling_tool.get_text_input()
        else:
            return textplus_tool.get_text_input()


class TextPlusComposition:
    def __init__(self, _composition: PyRemoteComposition):
        self._composition = _composition

    def get_settings(self, *other_tool_names) -> TextPlusSettings:
        tools = [self._composition.Template]

        for tool_name in other_tool_names:
            tool = self._composition.FindTool(tool_name)

            if tool is not None:
                tools.append(tool)

        return TextPlusSettings(self._composition.CopySettings(tools))

    def set_settings(self, settings: TextPlusSettings):
        ordered_dict_type = type(settings._settings["Tools"])

        for tool_name, tool_settings in settings._settings["Tools"].items():
            tool = self._composition.FindTool(tool_name)

            if tool is not None:
                sub_settings = {"Tools": ordered_dict_type([(tool_name, tool_settings)])}
                tool.LoadSettings(sub_settings)
