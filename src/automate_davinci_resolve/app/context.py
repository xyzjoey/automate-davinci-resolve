from typing import NamedTuple, Optional

from ..davinci.context import ResolveContext, TimelineContext


class AppContext(NamedTuple):
    resolve_context: ResolveContext


# TODO pass to pydantic.BaseModel directly when context is allow
# https://github.com/pydantic/pydantic/blob/main/docs/blog/pydantic-v2.md#validation-context-thumbsup
class InputContext(NamedTuple):
    timeline_context: Optional[TimelineContext]

    @classmethod
    def get(cls):
        if not hasattr(cls, "input_context"):
            cls.input_context = None

        return cls.input_context

    @classmethod
    def set(cls, input_context: "InputContext"):
        cls.input_context = input_context
