from typing import Any, NamedTuple, Optional

from .input_widgets.enum_widgets import SingleEnumValueWidget
from .input_widgets.file_widgets import LoadFileWidget
from .input_widgets.track_widgets import MultipleVideoTracksWidget
from ..app.actions import auto_textplus_style, import_textplus
from ..davinci.enums import ClipColor


class InputDefinition(NamedTuple):
    widget_type: Any
    args: dict = {}


class ActionDefinition(NamedTuple):
    group: str
    inputs: dict[str, InputDefinition]


class Definitions:
    actions = {
        auto_textplus_style.Action: ActionDefinition(
            group="Text+ Action",
            inputs={
                "ignored_tracks": InputDefinition(
                    widget_type=MultipleVideoTracksWidget,
                ),
            },
        ),
        import_textplus.Action: ActionDefinition(
            group="Text+ Action",
            inputs={
                "subtitle_file": InputDefinition(
                    widget_type=LoadFileWidget,
                    args={"file_types": [(".srt", ".srt")]},
                ),
                "gap_filler_clip_color": InputDefinition(
                    widget_type=SingleEnumValueWidget,
                    args={"enum_type": Optional[ClipColor]},
                ),
            },
        ),
    }
