from enum import Enum
from typing import Any, NamedTuple

from .custom_print import CustomPrint


class SpecialInputValue(Enum):
    HELP = 1
    QUIT = 2


class Choice(NamedTuple):
    value: Any
    description: str


class ChoiceInput:
    def __init__(self):
        self.choices = {}
        self.add_choice("?", SpecialInputValue.HELP, "print help")

    def add_choice(self, name, value, description=None):
        self.choices[name] = Choice(value=value, description=description)

    def print_help(self):
        for name, choice in self.choices.items():
            if name == "":
                print(f"(empty) - {choice.description}")
            else:
                print(f"{name} - {choice.description}")

    def ask_for_input(self, prompt):
        choice_name_hint = "/".join(self.choices.keys())
        full_prompt = f"{prompt} [{choice_name_hint}]: "

        while True:
            choice_name = input(full_prompt)
            choice_value, error = self.validate(choice_name)

            if choice_value is None:
                CustomPrint.print_error(str(error))
            elif choice_value == SpecialInputValue.HELP:
                self.print_help()
            else:
                return choice_value

    def validate(self, choice_name):
        choice = self.choices.get(choice_name)

        if choice is None:
            return None, Exception("Invalid input, type ? for help")

        return choice.value, None
