import os
from contextlib import contextmanager

import py.io


# TODO: use curses
class EscapeCode:
    SAVE_POSITION = "\x1b[s"
    MOVE_TO_SAVED_POSITION = "\x1b[u"
    ERASE_LINE = '\x1b[2K'
    MOVE_TO_BEGINNING_OF_LINE = "\x1b[0G"
    MOVE_TO_BEGINNING_OF_NEXT_LINE = "\x1b[1E"


class TerminalIO:
    instance = None

    def __init__(self):
        self.terminal_writer = py.io.TerminalWriter()
        self.bottom_info = {
            "collect_bottom_msg": False,
            "msg_args": None,
        }

    @classmethod
    def get(cls):
        if cls.instance is None:
            os.system("")  # enable ansi escape sequence in terminal
            cls.instance = cls()

        return cls.instance

    def print_normal(self, msg, end="\n"):
        self.__print(f"{msg}{end}")

    def print_error(self, msg, end="\n"):
        self.__print(f"{msg}{end}", red=True)

    def print_warning(self, msg, end="\n"):
        self.__print(f"{msg}{end}", yellow=True)

    def print_question(self, msg, end="\n"):
        self.__print(f"{msg}{end}", blue=True)

    def colored_input(self, msg):
        self.__print(f"{msg}", blue=True)
        return input()

    @contextmanager
    def at_bottom(self):
        self.bottom_info["collect_bottom_msg"] = True
        yield
        self.bottom_info["collect_bottom_msg"] = False

    def clear_bottom(self):
        self.bottom_info["msg_args"] = None

    def __print(self, msg, **kw):
        if self.bottom_info["collect_bottom_msg"]:
            self.bottom_info["msg_args"] = {"msg": msg, **kw}
            self.terminal_writer.write(msg, **kw)
        elif self.bottom_info["msg_args"] is not None:  # print above bottom
            print(EscapeCode.ERASE_LINE + EscapeCode.MOVE_TO_BEGINNING_OF_LINE, end="")
            self.terminal_writer.write(msg, **kw)
            self.terminal_writer.write(**self.bottom_info["msg_args"])
        else:
            self.terminal_writer.write(msg, **kw)


def print_normal(*args, **kw):
    TerminalIO.get().print_normal(*args, **kw)


def print_error(*args, **kw):
    TerminalIO.get().print_error(*args, **kw)


def print_warning(*args, **kw):
    TerminalIO.get().print_warning(*args, **kw)


def print_question(*args, **kw):
    TerminalIO.get().print_question(*args, **kw)


def colored_input(*args, **kw):
    return TerminalIO.get().colored_input(*args, **kw)


@contextmanager
def at_bottom(*args, **kw):
    with TerminalIO.get().at_bottom(*args, **kw):
        yield


def clear_bottom(*args, **kw):
    TerminalIO.get().clear_bottom(*args, **kw)
