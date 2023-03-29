import typing
from typing import Union

from .radiobutton_collection import RadioButtonCollection, RadioButtonOption
from ...utils import types


class SingleEnumValueWidget(RadioButtonCollection):
    def __init__(self, name, enum_type, selected=None, *args, **kw):
        super().__init__(name, *args, **kw)

        self.enum_type = enum_type

        is_union = types.is_union(enum_type)
        is_optional = types.is_optional(enum_type)
        underlying_types = [t for t in types.get_union_underlying_types(enum_type) if t is not type(None)] if is_union else [enum_type]

        options = []

        for underlying_type in underlying_types:
            for enum_value in underlying_type:
                options.append(RadioButtonOption(name=enum_value.name, value=enum_value))

        if is_optional:
            options = [RadioButtonOption(name="None", value=None)] + options

        self.reset(options=options, selected=selected)
