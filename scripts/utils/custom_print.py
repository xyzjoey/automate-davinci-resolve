import py.io


class CustomPrint:
    instance = None

    def __init__(self):
        self.terminal_writer = py.io.TerminalWriter()

    @classmethod
    def get(cls):
        if cls.instance is None:
            cls.instance = cls()

        return cls.instance

    @classmethod
    def print_error(cls, msg):
        cls.get().terminal_writer.write(f"{msg}\n", red=True)

    @classmethod
    def print_warning(cls, msg):
        cls.get().terminal_writer.write(f"{msg}\n", yellow=True)
