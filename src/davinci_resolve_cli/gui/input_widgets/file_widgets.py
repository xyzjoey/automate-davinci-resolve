import tkinter
from tkinter import filedialog

from customtkinter import CTkButton, CTkEntry

from ..widgets.named_frame import NamedFrame


class FileWidget(NamedFrame):
    def __init__(self, name, file_types, *args, **kw):
        super().__init__(name, *args, **kw)

        self.file_types = file_types

        self.entry = CTkEntry(
            master=self.content_frame,
            placeholder_text="file path",
        )
        self.entry.pack(side="left")

        self.button = CTkButton(
            master=self.content_frame,
            text="Browse",
            command=self.get_command(),
        )
        self.button.pack(side="left")

    def get_data(self):
        return self.entry.get()

    def get_command(self):
        def command():
            file_path = self.ask_file(filetypes=self.file_types)

            if file_path is not None and file_path != "":
                self.entry.delete(0, tkinter.END)
                self.entry.insert(0, file_path)

        return command


class LoadFileWidget(FileWidget):
    def ask_file(self, *args, **kw):
        return filedialog.askopenfilename(*args, **kw)


class SaveFileWidget(FileWidget):
    def ask_file(self, *args, **kw):
        return filedialog.asksaveasfilename(*args, **kw)
