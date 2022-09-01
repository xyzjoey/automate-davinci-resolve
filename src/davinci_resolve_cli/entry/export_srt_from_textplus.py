from davinci_resolve_cli.davinci.timeline_context import TimelineContext
from pydantic import BaseSettings, Field
import srt

from davinci_resolve_cli.davinci import textplus_utils
from davinci_resolve_cli.process.process_base import ProcessBase, ProcessResult
from davinci_resolve_cli.inputs.file_path_input import FilePathInput
from davinci_resolve_cli.utils import terminal_io


class Inputs(BaseSettings):
    subtitle_output_path: FilePathInput = Field(
        description="where to export subtitle file",
        default_factory=lambda: FilePathInput.ask_for_input("subtitle export", patterns=[".srt"])
    )


class Process(ProcessBase):
    def __init__(self):
        super().__init__(input_model=Inputs)

    def create_subtitles_from_timeline(self, timeline_context: TimelineContext):
        timecode_context = timeline_context.get_timecode_context()
        subtitles = []

        for track_context in timeline_context.iterate_tracks("video"):

            terminal_io.print_info(f"Processing {track_context}...")

            for item in track_context.timeline_items:
                textplus = textplus_utils.find_textplus(item)

                if textplus is None:
                    continue

                start = timecode_context.create_timecode_from_frame(item.GetStart(), start_timecode_is_applied=True)
                end = timecode_context.create_timecode_from_frame(item.GetEnd(), start_timecode_is_applied=True)
                text = textplus.GetInput("StyledText")

                subtitles.append(srt.Subtitle(
                    index=None,
                    start=start.get_timedelta(),
                    end=end.get_timedelta(),
                    content=text,
                    proprietary=f"video track {track_context.track_index}",
                ))

        return subtitles

    async def run_with_input(self, inputs: Inputs):
        subtitles = self.create_subtitles_from_timeline(self.resolve_context.get_current_timeline_context())

        file_content = srt.compose(subtitles)
        inputs.subtitle_output_path.get().write_text(file_content)

        return ProcessResult.Done


if __name__ == "__main__":
    Process().main()
