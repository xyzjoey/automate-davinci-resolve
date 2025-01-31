from pathlib import Path
from typing import Annotated

from pydantic import FilePath, AfterValidator
from pydantic_core.core_schema import no_info_after_validator_function
from pydantic.types import PathType
import srt


class SubtitleFileInput:
    def __init__(self, file_path: FilePath):
        self.file_path = file_path
        self.parsed: list[srt.Subtitle] = None

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return no_info_after_validator_function(
            Annotated[
                Path,
                PathType("file"),
                AfterValidator(cls.validate),
            ],
            handler(Path),
        )

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        file_path = v.resolve()

        try:
            with file_path.open(encoding="utf-8") as f:
                subtitles = list(srt.parse(f.read()))

                result_data = cls(file_path)
                result_data.parsed = subtitles

                return result_data

        except Exception as e:
            raise ValueError(f"Failed to parse subtitle file: {e}")
