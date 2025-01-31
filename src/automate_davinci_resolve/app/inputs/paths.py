from pathlib import Path
from typing import Annotated

from pydantic import AfterValidator


def validate_save_file_path(path):
    if path.exists() and not path.is_file():
        raise ValueError(f"{path.name} is a non file path")

    return path.resolve()


SaveFilePathInput = Annotated[Path, AfterValidator(validate_save_file_path)]
