from typing import TypeVar, Generic

from pydantic import ValidationError, parse_obj_as

from ..utils import terminal_io
from ..utils.errors import CancelledError


T = TypeVar("T")


class InputBase(Generic[T]):
    def __init__(self, data: T):
        self.data: T = data

    def __repr__(self):
        return f"{self.__class__.__name__}({str(self.get())})"

    def get(self):
        return self.data

    @classmethod
    def ask_input(cls, *args, **kw):
        while True:
            try:
                raw = cls.ask_raw_input(*args, **kw)
            except CancelledError:
                raise CancelledError()

            terminal_io.print_info(f"Received input: {raw}")

            try:
                return parse_obj_as(cls, raw)
            except ValidationError as validation_error:
                for error in validation_error.errors():
                    terminal_io.print_error(error["msg"])
