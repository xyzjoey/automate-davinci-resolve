from pydantic import ValidationError, parse_obj_as

from ..utils import terminal_io
from ..utils.errors import CancelledError


class InputBase:
    @classmethod
    def ask_input(cls, *args, **kw):
        while True:
            raw = cls.ask_raw_input(*args, **kw)

            if isinstance(raw, CancelledError):
                raise CancelledError()

            terminal_io.print_info(f"Received input: {raw}")

            try:
                return parse_obj_as(cls, raw)
            except ValidationError as validation_error:
                for error in validation_error.errors():
                    terminal_io.print_error(error["msg"])
