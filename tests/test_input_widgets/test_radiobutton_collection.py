from davinci_resolve_cli.gui.input_widgets.radiobutton_collection import RadioButtonCollection, RadioButtonOption


class TestRadioButtonCollection:
    def test_reset(self):
        radiobuttons = RadioButtonCollection("name", master=None)

        assert radiobuttons.get_data() == None

        radiobuttons.reset(
            options=[
                RadioButtonOption(value=1, name="A"),
                RadioButtonOption(value=2, name="B"),
                RadioButtonOption(value=3, name="C"),
            ],
            selected=3,
        )

        assert radiobuttons.get_data() == 3

        radiobuttons.reset(
            options=[
                RadioButtonOption(value=1, name="A"),
                RadioButtonOption(value=2, name="B"),
                RadioButtonOption(value=None, name="None"),
            ],
            selected=None,
        )

        assert radiobuttons.get_data() == None

    def test_invoke(self):
        radiobuttons = RadioButtonCollection("name", master=None)

        radiobuttons.reset(
            options=[
                RadioButtonOption(value=1, name="A"),
                RadioButtonOption(value=2, name="B"),
                RadioButtonOption(value=None, name="None"),
            ],
            selected=None,
        )

        assert radiobuttons.get_data() == None

        radiobuttons.radiobuttons[0].invoke()
        assert radiobuttons.get_data() == 1

        radiobuttons.radiobuttons[1].invoke()
        assert radiobuttons.get_data() == 2

        radiobuttons.radiobuttons[2].invoke()
        assert radiobuttons.get_data() == None
