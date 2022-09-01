import pytest
from pydantic import BaseModel

from davinci_resolve_cli.inputs.choice_input import Choice, ChoiceInput, ChoiceValue
from davinci_resolve_cli.inputs.integer_list_input import IntegerListInput


class TestInput:
    def test_choice_input(self):
        choice_input = ChoiceInput([
            Choice("choice_name_1", "choice_value_1", "description_1"),
            Choice("choice_name_2", "choice_value_2", "description_2"),
            Choice("?", ChoiceValue.HELP, "help"),
        ])

        choice_input.raw_value = "choice_name_1"
        assert ChoiceInput.validate(choice_input).get_value() == "choice_value_1"

        choice_input.raw_value = "choice_name_2"
        assert ChoiceInput.validate(choice_input).get_value() == "choice_value_2"

        choice_input.raw_value = "?"
        assert ChoiceInput.validate(choice_input).get_value() == ChoiceValue.HELP

        with pytest.raises(Exception):
            choice_input.raw_value = ""
            ChoiceInput.validate(choice_input)

    def test_integer_list_input(self):
        class Inputs(BaseModel):
            integer_list: IntegerListInput

        assert Inputs(integer_list="1").integer_list == [1]
        assert Inputs(integer_list="999").integer_list == [999]
        assert Inputs(integer_list="1,2,3,10,11,12").integer_list == [1, 2, 3, 10, 11, 12]

        with pytest.raises(Exception):
            Inputs(integer_list="")
