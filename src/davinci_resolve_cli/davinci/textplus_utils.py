from typing import Any, NamedTuple, Optional


class InputData(NamedTuple):
    value: Any
    expression: Optional[str]
    fusion_object: Any


def find_textplus(timeline_item):
    if timeline_item.GetFusionCompCount() == 0:
        return None

    comp = timeline_item.GetFusionCompByIndex(1)
    textplus = comp.FindToolByID("TextPlus")

    return textplus


def get_textplus_data(timeline_item) -> Optional[dict[str, InputData]]:
    textplus = find_textplus(timeline_item)

    if textplus is None:
        return None

    data = {}

    for input in textplus.GetInputList().values():
        input_id = input.GetAttrs("INPS_ID")
        value = textplus.GetInput(input_id)

        if hasattr(value, "ID") and value.ID == "Gradient":
            data[input_id] = InputData(value=value.Value, expression=input.GetExpression(), fusion_object=value)
        else:
            data[input_id] = InputData(value=value, expression=input.GetExpression(), fusion_object=None)

    return data


def set_textplus_data(timeline_item, textplus_data: Optional[dict[str, InputData]], exclude_data_ids=[]) -> bool:
    textplus = find_textplus(timeline_item)

    if textplus is None:
        return False

    for input in textplus.GetInputList().values():
        input_id = input.GetAttrs("INPS_ID")

        if input_id in exclude_data_ids:
            continue

        input_data = textplus_data.get(input_id)

        if input_data is None:
            continue

        if input_data.expression is not None:
            input.SetExpression(input_data.expression)
        else:
            if input.GetAttrs("INPS_DataType") == "Gradient":
                gradient = textplus.GetInput(input_id)
                if gradient is None:
                    textplus.SetInput(input_id, input_data.fusion_object)
                elif gradient.Value != input_data.value:
                    gradient.Value = input_data.value
            elif textplus.GetInput(input_id) != input_data.value:
                textplus.SetInput(input_id, input_data.value)

    return True


def set_textplus_data_only_style(timeline_item, textplus_data):
    return set_textplus_data(timeline_item, textplus_data, exclude_data_ids=["StyledText", "GlobalIn", "GlobalOut"])
