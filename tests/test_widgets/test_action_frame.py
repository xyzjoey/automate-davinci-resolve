from davinci_resolve_cli.gui.widgets.action_frame import ActionFrame


class TestActionFrame:
    def test_action_button(self, app):
        action = app.get_action("auto_textplus_style")
        action_frame = ActionFrame(app, action, master=None)

        assert action.is_starting is True

        action_frame.update(app.context)
        action_frame.action_button.invoke()

        assert action.is_starting is False

        action_frame.update(app.context)
        action_frame.action_button.invoke()

        assert action.is_starting is True

    def test_input_data(self, app, resolve_app):
        action = app.get_action("auto_textplus_style")
        action_frame = ActionFrame(app, action, master=None)

        resolve_app.mock_current_timeline(
            {
                "tracks": {
                    "video": {
                        1: {"items": []},
                        2: {"items": []},
                    }
                }
            }
        )

        app_context = app.update()
        action_frame.update(app_context)

        for checkbox in action_frame.input_widgets["ignored_tracks"].checkboxes:
            checkbox.toggle()

        assert action_frame.get_input_data() == {"ignored_tracks": [1, 2]}

        app.apply_inputs(action.name, action_frame.get_input_data())
        app_context = app.update()
        action_frame.update(app_context)

        assert action_frame.get_input_data() == {"ignored_tracks": [1, 2]}
