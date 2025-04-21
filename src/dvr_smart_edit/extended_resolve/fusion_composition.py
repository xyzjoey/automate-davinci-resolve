from pprint import pprint

from ..resolve_types import PyRemoteComposition, PyRemoteOperator


class FusionSettings:
    def __init__(self, _settings: dict):
        self._settings = _settings


class FusionComposition:
    def __init__(self, composition: PyRemoteComposition):
        self._composition = composition

    def get_settings(self, tools: list[PyRemoteOperator] = None) -> FusionSettings:
        if tools is None:
            tools = [tool for tool in self._composition.GetToolList().values() if tool.GetAttrs("TOOLS_RegID") != "MediaOut"]
            # skip MediaOut, as pasting MediaOut settings cause improper render cache

        settings = FusionSettings(self._composition.CopySettings(tools))

        return settings

    def set_settings(self, settings: FusionSettings):
        ordered_dict_type = type(settings._settings["Tools"])

        tools = {}
        modifiers = {}

        for tool_name, tool_settings in settings._settings["Tools"].items():
            is_modifier = tool_settings.get("ViewInfo") is None

            if is_modifier:
                modifiers[tool_name] = tool_settings
            else:
                tools[tool_name] = tool_settings

        for tool_name, tool_settings in tools.items():
            tool = self._composition.FindTool(tool_name)

            if tool is None:
                tool = self._composition.AddTool(tool_settings["__ctor"])
                tool.SetAttrs({"TOOLS_Name": tool_name})

            tool.LoadSettings({"Tools": ordered_dict_type([(tool_name, tool_settings), *modifiers.items()])})

        for tool_name, tool_settings in tools.items():
            for input_name, input_settings in tool_settings["Inputs"].items():
                src_operator_name = input_settings.get("SourceOp")

                if src_operator_name in tools:
                    from_tool = self._composition.FindTool(tool_name)
                    from_input = getattr(from_tool, input_name)

                    to_tool = self._composition.FindTool(src_operator_name)
                    to_output = getattr(to_tool, input_settings["Source"])

                    if str(from_input.GetConnectedOutput()) != str(to_output):
                        from_input.ConnectTo(to_output)
