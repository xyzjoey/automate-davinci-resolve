from automate_davinci_resolve.gui.input_widgets.checkbox_collection import CheckboxCollection, CheckboxOption


class TestCheckboxCollection:
    def test_reset(self):
        checkboxes = CheckboxCollection("name", master=None)

        assert checkboxes.get_data() == []

        checkboxes.reset(
            options=[
                CheckboxOption(value=1, name="A", selected=False),
                CheckboxOption(value=2, name="B", selected=True),
                CheckboxOption(value=3, name="C", selected=False),
                CheckboxOption(value=4, name="D", selected=True),
            ]
        )

        assert checkboxes.get_data() == [2, 4]

        checkboxes.reset(
            options=[
                CheckboxOption(value=1, name="A", selected=False),
                CheckboxOption(value=2, name="B", selected=True),
            ]
        )

        assert checkboxes.get_data() == [2]

    def test_toggle(self):
        checkboxes = CheckboxCollection("name", master=None)

        checkboxes.reset(
            options=[
                CheckboxOption(value=1, name="A", selected=False),
                CheckboxOption(value=2, name="B", selected=True),
                CheckboxOption(value=3, name="C", selected=False),
                CheckboxOption(value=4, name="D", selected=True),
            ]
        )

        for checkbox in checkboxes.checkboxes:
            checkbox.toggle()

        assert checkboxes.get_data() == [1, 3]
