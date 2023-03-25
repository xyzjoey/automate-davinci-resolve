from typing import Any, NamedTuple, Optional

from .track import Track


class Gradient(NamedTuple):
    fusion_gradient: Any
    value: dict


def find_textplus(timeline_item):
    if timeline_item.GetFusionCompCount() == 0:
        return None

    comp = timeline_item.GetFusionCompByIndex(1)
    textplus = comp.FindToolByID("TextPlus")

    return textplus


def get_textplus_data(timeline_item) -> Optional[dict]:
    textplus = find_textplus(timeline_item)

    if textplus is None:
        return None

    data = {}

    for input in textplus.GetInputList().values():
        input_id = input.GetAttrs("INPS_ID")
        value = textplus.GetInput(input_id)

        if hasattr(value, "ID") and value.ID == "Gradient":
            data[input_id] = Gradient(fusion_gradient=value, value=value.Value)
        else:
            data[input_id] = value

    return data


def set_textplus_data(timeline_item, textplus_data, exclude_data_ids=[]) -> bool:
    textplus = find_textplus(timeline_item)

    if textplus is None:
        return False

    for id, value in textplus_data.items():
        if id in exclude_data_ids:
            continue

        if isinstance(value, Gradient):
            gradient = textplus.GetInput(id)

            if gradient is None:
                textplus.SetInput(id, value.fusion_gradient)
            elif gradient.Value != value.value:
                gradient.Value = value.value
        else:
            if textplus.GetInput(id) != value:
                textplus.SetInput(id, value)

    return True


def set_textplus_data_only_style(timeline_item, textplus_data):
    return set_textplus_data(timeline_item, textplus_data, exclude_data_ids=["StyledText", "GlobalIn", "GlobalOut"])
