import tkinter
from tkinter import filedialog

from customtkinter import CTkButton, CTkEntry

from ..widgets.named_frame import NamedFrame


class LoadFileWidget(NamedFrame):
    def __init__(self, name, file_types, *args, **kw):
        super().__init__(name, *args, **kw)

        self.file_types = file_types

        self.entry = CTkEntry(
            master=self.content_frame,
            placeholder_text="file path",
            # width=120,
            # height=25,
            # border_width=2,
            # corner_radius=10,
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
            file_path = filedialog.askopenfilename(filetypes=self.file_types)

            if file_path is not None and file_path != "":
                self.entry.delete(0, tkinter.END)
                self.entry.insert(0, file_path)

        return command
