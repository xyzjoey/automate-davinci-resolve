import pprint
from typing import Any, NamedTuple

from pydantic import BaseSettings, Field

from davinci_utils.resolve_context import ResolveContext
from utils.terminal_io import TerminalIO


class CurrentFusionCompInput:
    def __init__(self, clip):
        self.clip = clip

    def get(self):
        return self.clip

    @classmethod
    def ask_for_input(cls):
        resolve_context = ResolveContext.get()
        track_count = resolve_context.project.GetCurrentTimeline().GetTrackCount("video")
        track_index = None

        if track_count == 1:
            try:
                return cls.validate(1)
            except Exception as e:
                TerminalIO.print_error(str(e))

        while True:
            track_index = TerminalIO.colored_input(f"Please enter a video track index (available track: 1 to {track_count})\n"
                                                    "for finding the clip at playhead as text style reference"
                                                    ": ")

            try:
                return cls.validate(track_index)
            except Exception as e:
                TerminalIO.print_error(str(e))

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        track_index = int(v)
        resolve_context = ResolveContext.get()

        if not resolve_context.is_valid_track_index("video", track_index):
            raise Exception(f"'{track_index}' is out of track range")

        timeline_item = resolve_context.find_current_timeline_item_at_track("video", track_index)

        if timeline_item is None:
            raise Exception("No clip at playhead location")

        print("Reference clip found:")
        print(f"\tName: {timeline_item.GetName()}")
        print(f"\tStart: {resolve_context.frame_to_timecode(timeline_item.GetStart())}")
        print(f"\tEnd: {resolve_context.frame_to_timecode(timeline_item.GetEnd())}")

        if timeline_item.GetFusionCompCount() == 0:
            raise Exception("Clip has no fusion composition")

        text_node = timeline_item.GetFusionCompByIndex(1).FindToolByID("TextPlus")

        if text_node is None:
            raise Exception("Clip has no Text+ node in 1st fusion composition")

        print(f"\tText: {repr(text_node.GetInput('StyledText'))}")

        return cls(timeline_item)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate


class VideoTrackIndicesInput:
    def __init__(self, track_indices):
        self.track_indices = sorted(list(set(track_indices)))

    def get(self):
        return self.track_indices

    @classmethod
    def ask_for_input(cls):
        resolve_context = ResolveContext.get()
        track_count = resolve_context.project.GetCurrentTimeline().GetTrackCount("video")
        track_indices = None

        if track_count == 1:
            try:
                return cls.validate([1])
            except Exception as e:
                TerminalIO.print_error(str(e))

        while True:
            track_indices = TerminalIO.colored_input(f"Please enter video track indices (available track: 1 to {track_count})\n"
                                                        "for applying text style\n"
                                                        "E.g. 2\n"
                                                        "E.g. 1,2,3\n"
                                                        ": ")

            try:
                return cls.validate(track_indices)
            except Exception as e:
                TerminalIO.print_error(str(e))

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        track_indices = None
        error = None

        try:
            track_indices = [int(v)]
        except Exception as e:
            error = e
        try:
            track_indices = [int(index) for index in v]
        except Exception as e:
            error = e
        try:
            track_indices = [int(index) for index in eval(v)]
        except Exception as e:
            error = e

        if track_indices is None:
            raise Exception(f"'{v}' is not a valid integer or list of integer ({str(error)})")

        resolve_context = ResolveContext.get()

        for i, track_index in enumerate(track_indices):
            if not resolve_context.is_valid_track_index("video", track_index):
                raise Exception(f"Item {i} (value={track_index}) is out of track range")

        return cls(track_indices)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate


class Inputs(BaseSettings):
    text_clip_input: CurrentFusionCompInput = Field(env="reference_track", default_factory=lambda: CurrentFusionCompInput.ask_for_input())
    track_indices_input: VideoTrackIndicesInput = Field(env="tracks", default_factory=lambda: VideoTrackIndicesInput.ask_for_input())


class TextPlusData(NamedTuple):
    value: Any
    is_gradient: bool
    is_default: bool
    default_value: Any


class Process:
    def __init__(self):
        self.resolve_context = ResolveContext.get()

    def get_fusion_text_data(self, timeline_item, exclude_ids):
        comp = timeline_item.GetFusionCompByIndex(1)
        text_node = comp.FindToolByID("TextPlus")
        default_text_node = comp.AddTool("TextPlus")

        data = {}

        for input in text_node.GetInputList().values():
            input_id = input.GetAttrs('INPS_ID')

            if input_id in exclude_ids:
                continue

            value = text_node.GetInput(input_id)
            default_value = default_text_node.GetInput(input_id)
            is_gradient = hasattr(value, "ID") and value.ID == "Gradient"

            if is_gradient:
                value = value.Value
                default_value = default_value if default_value is None else default_value.Value

            data[input_id] = TextPlusData(value=value, is_gradient=is_gradient, is_default=(value == default_value), default_value=default_value)

        default_text_node.Delete()

        print("Text style:")
        pprint.pprint({k: v.value for k, v in data.items() if not v.is_default and k in ["Font", "Style", "Size", "Red1", "Green1", "Blue1", "ShadingGradient1"]})

        return data

    def set_fusion_text(self, timeline_item, fusion_text_data):
        if timeline_item.GetFusionCompCount() == 0:
            return False

        comp = timeline_item.GetFusionCompByIndex(1)
        text_node = comp.FindToolByID("TextPlus")

        if text_node is None:
            return False

        for id, data in fusion_text_data.items():
            if data.is_gradient:
                gradient = text_node.GetInput(id)

                if gradient is not None and gradient.Value != data.value:
                    gradient.Value = data.value
            else:
                if text_node.GetInput(id) != data.value:
                    text_node.SetInput(id, data.value)

        return True

    def set_fusion_text_in_tracks(self, track_indices, fusion_text_data):
        timeline = self.resolve_context.project.GetCurrentTimeline()

        for track_index in track_indices:
            timeline_items = timeline.GetItemListInTrack("video", track_index)
            applied_count = 0
            unapplied_count = 0

            for i, timeline_item in enumerate(timeline_items):
                print(f"Applying fusion text style to {i + 1}/{len(timeline_items)} clip in video track {track_index}...", end="\r")

                if self.set_fusion_text(timeline_item, fusion_text_data):
                    applied_count += 1
                else:
                    unapplied_count += 1

            print()

            if unapplied_count > 0:
                print(f"Applied to {applied_count} clips in video track {track_index}")
                print(f"{unapplied_count} clips are skipped because cannot find Text+ node in 1st fusion composition")

        print("Done")

    def run_with_inputs(self, inputs: Inputs):
        fusion_text_data = self.get_fusion_text_data(inputs.text_clip_input.get(), exclude_ids=["StyledText"])
        self.set_fusion_text_in_tracks(inputs.track_indices_input.get(), fusion_text_data)

    def run(self):
        self.resolve_context.update()
        inputs = Inputs()
        self.run_with_inputs(inputs)

    def main(self):
        self.run()


if __name__ == "__main__":
    Process().main()
