from typing import Any, NamedTuple, Optional

from customtkinter import CTkCheckBox

from ..widgets.named_frame import NamedScrollableFrame


class CheckboxOption(NamedTuple):
    name: str
    value: Any
    selected: bool


class CheckboxCollection(NamedScrollableFrame):
    def __init__(self, name, *args, **kw):
        super().__init__(name, *args, **kw)

        self.options: list[CheckboxOption] = []
        self.checkboxes: list[CTkCheckBox] = []
        self.reset([])

    def reset(self, options: list[CheckboxOption]):
        if self.options == options:
            return

        # if self.options is None:

        # if options is None:

        for i, option in enumerate(options):
            if i < len(self.checkboxes):
                self.checkboxes[i].configure(
                    text=option.name,
                    command=self.get_command(i),
                )

                if option.selected is True:
                    self.checkboxes[i].select()
                else:
                    self.checkboxes[i].deselect()

                if i >= len(self.options):
                    self.checkboxes[i].pack(side="top")
            else:
                checkbox = CTkCheckBox(
                    master=self.content_frame,
                    text=option.name,
                    command=self.get_command(i),
                )

                if option.selected is True:
                    checkbox.select()
                else:
                    checkbox.deselect()

                checkbox.pack(side="top")
                self.checkboxes.append(checkbox)

        if len(options) < len(self.checkboxes):
            for i in range(len(options), len(self.checkboxes)):
                self.checkboxes[i].pack_forget()

        self.options = options

    def get_data(self):
        return [option.value for option in self.options if option.selected is True]

    def get_command(self, index):
        def command():
            option = self.options[index]
            self.options[index] = option._replace(selected=not option.selected)

        return command
