from tkinter import Tk, filedialog

from pydantic import BaseSettings

from . import terminal_io


class FileIOSettings(BaseSettings):
    file_dialog: bool = False

    class Config:
        env_file = ".env"


class FileIO:
    settings = FileIOSettings()

    @classmethod
    def ask_load_file(cls, title: str, patterns: list[str], **kw):
        if cls.settings.file_dialog:
            root = Tk()
            root.withdraw()

            kw["filetypes"] = [(p, p) for p in patterns]

            terminal_io.print_question(f"Please select the file path for {title} from file dialog")
            return filedialog.askopenfilename(title=title, **kw)

        else:
            return terminal_io.prompt(f"Please enter the file path for {title}:")

    @classmethod
    def ask_save_file(cls, title: str, patterns: list[str], **kw):
        if cls.settings.file_dialog:
            root = Tk()
            root.withdraw()

            kw["filetypes"] = [(p, p) for p in patterns]

            default_filename = "*" if len(patterns) == 0 else "*" + patterns[0]

            terminal_io.print_question(f"Please select the file path for {title} from file dialog")
            return filedialog.asksaveasfilename(title=title, initialfile=default_filename, **kw)

        else:
            return terminal_io.prompt(f"Please enter the file path for {title}:")