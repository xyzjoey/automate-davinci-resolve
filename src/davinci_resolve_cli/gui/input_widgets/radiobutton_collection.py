from typing import Any, NamedTuple, Optional

from customtkinter import CTkRadioButton

from ..widgets.named_frame import NamedScrollableFrame


class RadioButtonOption(NamedTuple):
    name: str
    value: Any


class RadioButtonCollection(NamedScrollableFrame):
    def __init__(self, name, *args, **kw):
        super().__init__(name, *args, **kw)

        self.options: list[RadioButtonOption] = []
        self.selected_index: Optional[int] = None
        self.radiobuttons: list[CTkRadioButton] = []
        self.reset(options=[], selected=None)

    def reset(self, options: list[RadioButtonOption], selected: Any):
        selected_index = next((i for i in range(len(options)) if options[i].value == selected), None)

        if self.options == options and self.selected_index == selected_index:
            return

        # if self.options is None:

        # if options is None:

        self.selected_index = None

        for i, option in enumerate(options):
            if i < len(self.radiobuttons):
                self.radiobuttons[i].configure(
                    text=option.name,
                    command=self.get_command(i),
                )

                if selected == option.value:
                    self.selected_index = i
                    self.radiobuttons[i].select()
                else:
                    self.radiobuttons[i].deselect()

                if i >= len(self.options):
                    self.radiobuttons[i].pack(side="top")
            else:
                radiobutton = CTkRadioButton(
                    master=self.content_frame,
                    text=option.name,
                    command=self.get_command(i),
                )

                if selected == option.value:
                    self.selected_index = i
                    radiobutton.select()
                else:
                    radiobutton.deselect()

                radiobutton.pack(side="top")
                self.radiobuttons.append(radiobutton)

        if len(options) < len(self.radiobuttons):
            for i in range(len(options), len(self.radiobuttons)):
                self.radiobuttons[i].pack_forget()

        self.options = options

    def get_data(self):
        if self.selected_index is None:
            return None

        return self.options[self.selected_index].value

    def get_command(self, index):
        def command():
            if self.selected_index is not None and self.selected_index != index:
                self.radiobuttons[self.selected_index].deselect()

            self.selected_index = index

        return command
