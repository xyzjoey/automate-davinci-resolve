from pathlib import Path

from pydantic import ValidationError

from ..utils import terminal_io
from ..utils.errors import CancelledError
from ..utils.file_io import FileIO


class FilePath:
    def __init__(self, file_path: Path):
        self.file_path: Path = file_path

    def __repr__(self):
        return f"{self.__class__.__name__}({str(self.file_path)})"

    def get(self):
        return self.file_path

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


class LoadFilePath(FilePath):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        v = super().validate(v)

        if not v.get().is_file():
            raise ValueError(f"{v.get()} is not a file path or does not exist")

        return v

    @classmethod
    def ask_for_input(cls, title, patterns):
        while True:
            file_path = FileIO.ask_load_file(title=title, patterns=patterns)

            if file_path == "":
                raise CancelledError()

            try:
                return cls.validate(file_path)
            except ValidationError as e:
                terminal_io.print_error(str(e))


class SaveFilePath(FilePath):
    @classmethod
    def __get_validators__(cls):
        yield super().validate

    @classmethod
    def ask_for_input(cls, title, patterns):
        while True:
            file_path = FileIO.ask_save_file(title=title, patterns=patterns)

            if file_path == "":
                raise CancelledError()

            try:
                return cls.validate(file_path)
            except ValidationError as e:
                terminal_io.print_error(str(e))
