import copy
from pathlib import Path
import tempfile
from typing import Any, NamedTuple, Optional

from .parser import FusionSettingParser


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


def get_settings(textplus):
    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_path = Path(f"{temp_dir_name}/temp.setting")

        if not textplus.SaveSettings(str(temp_path)):
            return None

        return FusionSettingParser.parse(temp_path.read_text(encoding="utf-8"))


def set_settings(textplus, settings, exclude=[]):
    if len(exclude) == 0:
        new_settings = settings
    else:
        new_settings = copy.deepcopy(settings)
        current_settings = get_settings(textplus)

        for name in exclude:
            current_settings_textplus = next(v for v in current_settings["Tools"].values() if type(v) is dict and v.get("__ctor") == "TextPlus")
            new_settings_textplus = next(v for v in new_settings["Tools"].values() if type(v) is dict and v.get("__ctor") == "TextPlus")

            if name in current_settings_textplus["Inputs"]:
                if "SourceOp" in new_settings_textplus["Inputs"][name]:
                    quoted_source_name = new_settings_textplus["Inputs"][name]["SourceOp"]
                    source_name = quoted_source_name[1:-1]
                    new_settings["Tools"].pop(source_name)

                input = current_settings_textplus["Inputs"][name]
                new_settings_textplus["Inputs"][name] = input

                if "SourceOp" in input:
                    quoted_source_name = input["SourceOp"]
                    source_name = quoted_source_name[1:-1]
                    new_settings["Tools"][source_name] = current_settings["Tools"][source_name]
            else:
                new_settings_textplus["Inputs"].pop(name)

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_path = Path(f"{temp_dir_name}/temp.setting")
        temp_path.write_text(FusionSettingParser.compose(new_settings), encoding="utf-8")
        success = textplus.LoadSettings(str(temp_path))
        return success
