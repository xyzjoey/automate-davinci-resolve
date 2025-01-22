from typing import Any, NamedTuple, Optional, Union

from .input_widgets.enum_widgets import SingleEnumValueWidget
from .input_widgets.file_widgets import LoadFileWidget, SaveFileWidget
from .input_widgets.track_widgets import MultipleVideoTracksWidget
from ..app.actions import (
    auto_textplus_style,
    export_textplus,
    import_textplus,
    print_clip_info,
    sync_textplus_style,
)
from ..app.enums import ExtraChoice
from ..davinci.enums import ClipColor
from ..utils import types


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
        sync_textplus_style.Action: ActionDefinition(
            group="Text+ Action",
            inputs={
                "tracks": InputDefinition(
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
            },
        ),
        export_textplus.Action: ActionDefinition(
            group="Text+ Action",
            inputs={
                "subtitle_file": InputDefinition(
                    widget_type=SaveFileWidget,
                    args={"file_types": [(".srt", ".srt")]},
                ),
                "replace_mode_color": InputDefinition(
                    widget_type=SingleEnumValueWidget,
                    args={
                        "enum_type": Optional[Union[ExtraChoice, ClipColor]],
                        "selected": types.get_pydantic_field_default(export_textplus.Inputs, "replace_mode_color"),
                    },
                ),
                "merge_mode_color": InputDefinition(
                    widget_type=SingleEnumValueWidget,
                    args={
                        "enum_type": Optional[Union[ExtraChoice, ClipColor]],
                        "selected": types.get_pydantic_field_default(export_textplus.Inputs, "merge_mode_color"),
                    },
                ),
                "ignore_mode_color": InputDefinition(
                    widget_type=SingleEnumValueWidget,
                    args={
                        "enum_type": Optional[Union[ExtraChoice, ClipColor]],
                        "selected": types.get_pydantic_field_default(export_textplus.Inputs, "ignore_mode_color"),
                    },
                ),
            },
        ),
        # print_clip_info.Action: ActionDefinition(
        #     group="Dev",
        #     inputs={
        #         "track": InputDefinition(
        #             widget_type=MultipleVideoTracksWidget,
        #         ),
        #     },
        # ),
    }
