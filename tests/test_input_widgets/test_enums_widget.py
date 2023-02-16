from enum import Enum
from typing import Optional

from davinci_resolve_cli.gui.input_widgets.enum_widgets import SingleEnumValueWidget, RadioButtonOption


class MyEnum(Enum):
    A = "a"
    B = "b"
    C = "c"


class TestSingleEnumValueWidget:
    def test_init(self):
        enum_widget = SingleEnumValueWidget(name="test", enum_type=MyEnum, master=None)

        assert enum_widget.options == [
            RadioButtonOption(value=MyEnum.A, name="A"),
            RadioButtonOption(value=MyEnum.B, name="B"),
            RadioButtonOption(value=MyEnum.C, name="C"),
        ]

    def test_optional(self):
        enum_widget = SingleEnumValueWidget(name="test", enum_type=Optional[MyEnum], master=None)

        assert enum_widget.options == [
            RadioButtonOption(value=None, name="None"),
            RadioButtonOption(value=MyEnum.A, name="A"),
            RadioButtonOption(value=MyEnum.B, name="B"),
            RadioButtonOption(value=MyEnum.C, name="C"),
        ]
