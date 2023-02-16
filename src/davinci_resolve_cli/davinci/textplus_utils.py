from typing import Any, NamedTuple, Optional

from .track import Track
from ..utils import terminal_io


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


def apply_textplus_style_to(track: Track, textplus_data, filter_if=lambda _: False, print_progress=False):
    applied_items = []
    skipped_items = []
    # filtered_items = []

    for i, timeline_item in enumerate(track.timeline_items):
        if print_progress:
            terminal_io.print_info(f"Applying Text+ style to {i + 1}/{len(track.timeline_items)} clip in video track {track.index}...", end="\r")

        if not filter_if(timeline_item):
            if set_textplus_data_only_style(timeline_item, textplus_data):
                applied_items.append(timeline_item)
            else:
                skipped_items.append(timeline_item)
        # else:
        #     filtered_items.append(timeline_item)

    if print_progress:
        terminal_io.print_info("")

    applied_count = len(applied_items)
    skipped_count = len(skipped_items)

    if skipped_count == 0:
        terminal_io.print_info(f"Applied to {applied_count} clips in video track {track.index}.")
    else:
        terminal_io.print_info(f"Applied to {applied_count} clips in video track {track.index}. ({skipped_count} clips without Text+ are skipped)")

    return applied_items


# def print_textplus(textplus_data):
#     print(f"\tText: {repr(textplus_data['StyledText'])}")
#     print(f"\tFont: {textplus_data['Font']} ({textplus_data['Style']})")
#     print(f"\tSize: {textplus_data['Size']}")
#     print(f"\tColor: ({textplus_data['Red1']}, {textplus_data['Green1']}, {textplus_data['Blue1']})")
