from typing import Type

from pydantic import BaseModel

from ...davinci.enums import ResolveStatus


class ActionBase:
    def __init__(
        self,
        name: str,
        display_name: str,
        description: str,
        required_status: ResolveStatus,
        input_model: Type[BaseModel] = None,
    ):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.required_status = required_status
        self.input_model = input_model

    def __repr__(self):
        return f"Action '{self.display_name}'"
