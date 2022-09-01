from pathlib import Path

from pydantic import ValidationError

from ..utils import terminal_io
from ..utils.errors import CancelledError
from ..utils.file_io import FileIO


class FilePathInput:
    def __init__(self, file_path: Path):
        self.file_path: Path = file_path

    def get(self):
        return self.file_path

    def __repr__(self):
        return f"FilePathInput('{self.file_path.name}')"

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        if v == "":
            raise CancelledError()

        file_path = v

        if not isinstance(v, Path):
            file_path = Path(v)

        file_path = file_path.resolve()

        if not file_path.exists():
            raise ValidationError(f"File '{file_path.name}' does not exist")

        if not file_path.is_file():
            raise ValidationError(f"'{file_path.name}' is not a file path")

        return cls(file_path)

    @classmethod
    def ask_for_input(cls, title, patterns):
        while True:
            file_path = FileIO.ask_file(title=title, patterns=patterns)

            try:
                return cls.validate(file_path)
            except ValidationError as e:
                terminal_io.print_error(str(e))
