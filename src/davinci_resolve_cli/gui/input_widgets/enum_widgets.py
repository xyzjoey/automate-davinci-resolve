from .radiobutton_collection import RadioButtonCollection, RadioButtonOption
from ...utils import types


class SingleEnumValueWidget(RadioButtonCollection):
    def __init__(self, name, enum_type, *args, **kw):
        super().__init__(name, *args, **kw)

        self.enum_type = enum_type

        is_optional = types.is_optional(enum_type)
        underlying_type = enum_type if not is_optional else types.get_optional_underlying_type(enum_type)

        options = [RadioButtonOption(name=enum_value.name, value=enum_value) for enum_value in underlying_type]

        if is_optional:
            options = [RadioButtonOption(name="None", value=None)] + options

        self.reset(options=options, selected=None)
