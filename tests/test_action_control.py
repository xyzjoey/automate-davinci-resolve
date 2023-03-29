from pydantic import BaseModel

from davinci_resolve_cli.app.actions.action_base import ActionBase
from davinci_resolve_cli.app.actions.action_control import ActionControl
from davinci_resolve_cli.davinci.enums import ResolveStatus
from davinci_resolve_cli.davinci.context import TimelineContext


class MyInput(BaseModel):
    text: str = ""


class MyAction(ActionBase):
    def __init__(self):
        super().__init__(
            name="",
            display_name="test",
            description="",
            required_status=ResolveStatus.TimelineOpened,
            input_model=MyInput,
        )

        self.update_count = 0
        self.start_count = 0
        self.last_input_data = None

    def start(self, input_data):
        self.start_count += 1
        self.last_input_data = input_data


class MyBackgroundAction(MyAction):
    def update(self, input_data):
        self.update_count += 1
        self.last_input_data = input_data


class TestActionControl:
    dummy_timeline_context = TimelineContext(id="", name="", video_tracks={})

    def test_status(self, app_settings, resolve_app):
        action_control = ActionControl(MyAction())
        background_action_control = ActionControl(MyBackgroundAction())
        dummy_args = (app_settings, ResolveStatus.TimelineOpened, resolve_app, self.dummy_timeline_context, {})

        assert not action_control.is_starting
        assert background_action_control.is_starting

        action_control.start(*dummy_args)
        background_action_control.start(*dummy_args)

        assert not action_control.is_starting
        assert background_action_control.is_starting

        action_control.stop()
        background_action_control.stop()

        assert not action_control.is_starting
        assert not background_action_control.is_starting

        action_control.start(*dummy_args)
        background_action_control.start(*dummy_args)

        assert not action_control.is_starting
        assert background_action_control.is_starting

    def test_start(self, app_settings, resolve_app):
        action_control = ActionControl(MyAction())
        background_action_control = ActionControl(MyBackgroundAction())
        dummy_args = (resolve_app, self.dummy_timeline_context, {})

        action_control.start(app_settings, ResolveStatus.ProjectOpened, *dummy_args)
        background_action_control.start(app_settings, ResolveStatus.ProjectOpened, *dummy_args)

        assert action_control.action.start_count == 0
        assert background_action_control.action.start_count == 0

        action_control.start(app_settings, ResolveStatus.TimelineOpened, *dummy_args)
        background_action_control.start(app_settings, ResolveStatus.TimelineOpened, *dummy_args)

        assert action_control.action.start_count == 1
        assert background_action_control.action.start_count == 1

    def test_validate_input(self, app_settings, resolve_app):
        action_control = ActionControl(MyAction())
        dummy_args = (app_settings, ResolveStatus.TimelineOpened, resolve_app, self.dummy_timeline_context)

        action_control.start(*dummy_args, input_data={"text": None})
        assert action_control.action.last_input_data == None

        action_control.start(*dummy_args, input_data={"text": "abc"})
        assert action_control.action.last_input_data == MyInput(text="abc")

    def test_update_with_input_data(self, app_settings, resolve_app):
        action_control = ActionControl(MyBackgroundAction())
        dummy_start_args = (app_settings, ResolveStatus.TimelineOpened, resolve_app, self.dummy_timeline_context)
        dummy_update_args = (ResolveStatus.TimelineOpened, resolve_app, self.dummy_timeline_context, None)

        action_control.start(*dummy_start_args, input_data={"text": None})
        action_control.update(*dummy_update_args)
        assert action_control.action.last_input_data == MyInput()

        action_control.start(*dummy_start_args, input_data={"text": "abc"})
        action_control.update(*dummy_update_args)
        assert action_control.action.last_input_data == MyInput(text="abc")
