from pydantic import BaseSettings, Field

from davinci_resolve_cli.utils import terminal_io
from davinci_resolve_cli.davinci import textplus_utils
from davinci_resolve_cli.davinci.resolve_context import ResolveContext, ResolveStatus
from davinci_resolve_cli.davinci.track_context import TrackContext
from davinci_resolve_cli.utils.input import IntegerListInput


class CurrentTimelineTextPlusInput:
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
                terminal_io.print_error(str(e))

        while True:
            track_index = terminal_io.colored_input(f"Please enter a video track index (available track: 1 to {track_count})\n"
                                                    "for finding the Text+ at playhead as style reference"
                                                    ": ")

            try:
                return cls.validate(track_index)
            except Exception as e:
                terminal_io.print_error(str(e))

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        track_index = int(v)
        resolve_context = ResolveContext.get()

        if not resolve_context.is_valid_track_index("video", track_index):
            raise Exception(f"'{track_index}' is out of track range")

        print(f"Finding reference clip at playhead in video track {track_index} ('{resolve_context.project.GetCurrentTimeline().GetTrackName('video', track_index)}')...")

        timeline_item = resolve_context.find_current_timeline_item_at_track("video", track_index)

        if timeline_item is None:
            raise Exception("No clip at playhead location")

        print("Reference clip found:")
        print(f"\tName: {timeline_item.GetName()}")
        print(f"\tStart: {resolve_context.frame_to_timecode(timeline_item.GetStart())}")
        print(f"\tEnd: {resolve_context.frame_to_timecode(timeline_item.GetEnd())}")

        if timeline_item.GetFusionCompCount() == 0:
            raise Exception("Clip has no fusion composition")

        textplus = timeline_item.GetFusionCompByIndex(1).FindToolByID("TextPlus")

        if textplus is None:
            raise Exception("Clip has no Text+ node in 1st fusion composition")

        print(f"\tText: {repr(textplus.GetInput('StyledText'))}")

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
                terminal_io.print_error(str(e))

        while True:
            track_indices = terminal_io.colored_input(f"Please enter video track indices (available track: 1 to {track_count})\n"
                                                        "for applying Text+ style\n"
                                                        "E.g. 2\n"
                                                        "E.g. 1,2,3\n"
                                                        ": ")

            try:
                return cls.validate(track_indices)
            except Exception as e:
                terminal_io.print_error(str(e))

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        track_indices = IntegerListInput.validate(v)
        resolve_context = ResolveContext.get()

        for i, track_index in enumerate(track_indices):
            if not resolve_context.is_valid_track_index("video", track_index):
                raise Exception(f"Item {i} (value={track_index}) is out of track range")

        return cls(track_indices)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate


class Inputs(BaseSettings):
    timeline_textplus_input: CurrentTimelineTextPlusInput = Field(env="reference_track", default_factory=lambda: CurrentTimelineTextPlusInput.ask_for_input())
    track_indices_input: VideoTrackIndicesInput = Field(env="tracks", default_factory=lambda: VideoTrackIndicesInput.ask_for_input())


class Process:
    def __init__(self):
        self.resolve_context = ResolveContext.get()

    def set_textplus_in_tracks(self, track_indices, textplus_data):
        timeline = self.resolve_context.project.GetCurrentTimeline()

        for track_index in track_indices:
            track_context = TrackContext.get(timeline, "video", track_index)
            textplus_utils.apply_textplus_style_to(track_context, textplus_data, print_progress=True)

        print("Done")

    def run_with_inputs(self, inputs: Inputs):
        textplus_data = textplus_utils.get_textplus_data(inputs.timeline_textplus_input.get())

        print("Text+ info:")
        textplus_utils.print_textplus(textplus_data)

        self.set_textplus_in_tracks(inputs.track_indices_input.get(), textplus_data)

    def run(self):
        status = self.resolve_context.update()

        if status == ResolveStatus.NotAvail:
            terminal_io.print_error("Failed to load Davinci Resolve script app. Is Davinci Resolve running?")
        elif status == ResolveStatus.ProjectAvail:
            terminal_io.print_error("Davinci Resolve project is not opened")
        else:
            inputs = Inputs()
            self.run_with_inputs(inputs)

    def main(self):
        self.run()


if __name__ == "__main__":
    Process().main()
