from enum import Enum
from typing import Any, NamedTuple

from . import terminal_io


class ChoiceValue(Enum):
    HELP = 0
    HELP_MORE = 1
    QUIT = 2
    PAUSE = 3


class Choice(NamedTuple):
    name: str
    value: Any
    description: str


class ChoiceInput:
    def __init__(self, choices):
        self.choices = {c.name: c for c in choices}

        self.raw_value = None
        self.selected_choice = None

    def get_value(self):
        return self.selected_choice.value if self.selected_choice is not None else None

    def get_choice_names(self):
        return self.choices.keys()

    def print_help(self):
        for name, choice in self.choices.items():
            if name == "":
                print(f"(empty) - {choice.description}")
            else:
                print(f"{name} - {choice.description}")

    @classmethod
    def ask_for_input(cls, prompt, choices) -> "ChoiceInput":
        choice_input = cls(choices)

        choice_name_hint = "/".join(choice_input.get_choice_names())
        full_prompt = f"{prompt} [{choice_name_hint}]: "

        while True:
            choice_input.raw_value = terminal_io.colored_input(full_prompt)

            try:
                return cls.validate(choice_input)
            except Exception as e:
                terminal_io.print_error(str(e))

    @classmethod
    def validate(cls, choice_input) -> "ChoiceInput":
        choice_input.selected_choice = choice_input.choices.get(choice_input.raw_value)

        if choice_input.selected_choice is None:
            raise Exception("Invalid input, type ? for help")

        return choice_input
