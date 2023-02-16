from pathlib import Path

from .input_base import InputBase
from ..utils.errors import CancelledError
from ..utils.file_io import FileIO


class FilePathInput(InputBase[Path]):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        path = Path(v)
        path = path.resolve()

        if path.is_dir():
            raise ValueError(f"'{path.name}' is a directory")

        return cls(path)


class LoadFilePathInput(FilePathInput):
    def __init__(self, file_path: Path, parsed_data=None):
        super().__init__(file_path)
        self.parsed_data = parsed_data

    def get_parsed(self):
        return self.parsed_data

    @classmethod
    def __get_validators__(cls):
        yield from super().__get_validators__()
        yield cls.validate_path

        if hasattr(cls, "parse"):
            yield cls.parse

    @classmethod
    def validate_path(cls, v: "LoadFilePathInput"):
        if not v.get().is_file():
            raise ValueError(f"{v.get()} is not a valid file path or does not exist")

        return v

    @classmethod
    def ask_raw_input(cls, title, patterns):
        file_path = FileIO.ask_load_file(title=title, patterns=patterns)

        if file_path == "":
            raise CancelledError()

        return file_path


class SaveFilePathInput(FilePathInput):
    @classmethod
    def ask_raw_input(cls, title, patterns):
        file_path = FileIO.ask_save_file(title=title, patterns=patterns)

        if file_path == "":
            raise CancelledError()

        return file_path
