from typing import Any, NamedTuple, Optional


class InputData(NamedTuple):
    data_type: str
    value: Any
    expression: Optional[str]
    fusion_object: Any


def find_textplus(timeline_item):
    if timeline_item.GetFusionCompCount() == 0:
        return None

    comp = timeline_item.GetFusionCompByIndex(1)
    textplus = comp.FindToolByID("TextPlus")

    return textplus


def save_settings(textplus, settings_path: str):
    return textplus.SaveSettings(settings_path)


def load_settings(textplus, settings_path: str, exclude_data_ids=[]):
    # TODO: try modify settings file instead of looping InputList

    preserved_data = {}

    for id in exclude_data_ids:
        value = textplus.GetInput(id)

        if hasattr(value, "ID") and value.ID == "Gradient":
            preserved_data[id] = InputData(data_type="Gradient", value=value.Value, expression=None, fusion_object=value)
        else:
            preserved_data[id] = InputData(data_type=..., value=value, expression=None, fusion_object=None)

    success = textplus.LoadSettings(settings_path)

    if not success:
        return False

    for id, input_data in preserved_data.items():
        if input_data.data_type == "Gradient":
            gradient = textplus.GetInput(id)
            if gradient is None:
                textplus.SetInput(id, input_data.fusion_object)
            else:
                gradient.Value = input_data.value
        else:
            textplus.SetInput(id, input_data.value)

    return success
