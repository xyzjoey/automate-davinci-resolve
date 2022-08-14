from typing import Any, NamedTuple

from .track_context import TrackContext
from .. import terminal_io


class Gradient(NamedTuple):
    fusion_gradient: Any
    value: dict


def get_textplus_data(timeline_item):
    comp = timeline_item.GetFusionCompByIndex(1)
    textplus = comp.FindToolByID("TextPlus")

    data = {}

    for input in textplus.GetInputList().values():
        input_id = input.GetAttrs('INPS_ID')
        value = textplus.GetInput(input_id)

        if hasattr(value, "ID") and value.ID == "Gradient":
            data[input_id] = Gradient(fusion_gradient=value, value=value.Value)
        else:
            data[input_id] = value

    return data


def set_textplus_data(timeline_item, textplus_data, exclude_data_ids=[]):
    if timeline_item.GetName() is None:  # clip is deleted
        return False

    if timeline_item.GetFusionCompCount() == 0:
        return False

    comp = timeline_item.GetFusionCompByIndex(1)
    textplus = comp.FindToolByID("TextPlus")

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


def apply_textplus_style_to(track_context: TrackContext, textplus_data, filter_if=lambda _: False, print_progress=False):
    applied_items = []
    skipped_items = []
    # filtered_items = []

    for i, timeline_item in enumerate(track_context.items):
        if print_progress:
            terminal_io.print_normal(f"Applying Text+ style to {i + 1}/{len(track_context.items)} clip in video track {track_context.index}...", end="\r")

        if not filter_if(timeline_item):
            if set_textplus_data_only_style(timeline_item, textplus_data):
                applied_items.append(timeline_item)
            else:
                skipped_items.append(timeline_item)
        # else:
        #     filtered_items.append(timeline_item)

    if print_progress:
        terminal_io.print_normal("")

    applied_count = len(applied_items)
    skipped_count = len(skipped_items)

    if skipped_count == 0:
        terminal_io.print_normal(f"Applied to {applied_count} clips in video track {track_context.index}.")
    else:
        terminal_io.print_normal(f"Applied to {applied_count} clips in video track {track_context.index}. ({skipped_count} clips without Text+ are skipped)")

    return applied_items


def print_textplus(textplus_data):
    print(f"\tText: {repr(textplus_data['StyledText'])}")
    print(f"\tFont: {textplus_data['Font']} ({textplus_data['Style']})")
    print(f"\tSize: {textplus_data['Size']}")
    print(f"\tColor: ({textplus_data['Red1']}, {textplus_data['Green1']}, {textplus_data['Blue1']})")

