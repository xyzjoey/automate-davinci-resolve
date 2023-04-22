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
        common_args = (app_settings, ResolveStatus.TimelineOpened, resolve_app, self.dummy_timeline_context, {})

        assert not action_control.is_starting
        assert background_action_control.is_starting

        action_control.start(*common_args)
        background_action_control.start(*common_args)

        assert not action_control.is_starting
        assert background_action_control.is_starting

        action_control.stop()
        background_action_control.stop()

        assert not action_control.is_starting
        assert not background_action_control.is_starting

        action_control.start(*common_args)
        background_action_control.start(*common_args)

        assert not action_control.is_starting
        assert background_action_control.is_starting

    def test_start(self, app_settings, resolve_app):
        action_control = ActionControl(MyAction())
        background_action_control = ActionControl(MyBackgroundAction())
        common_args = (resolve_app, self.dummy_timeline_context, {})

        action_control.start(app_settings, ResolveStatus.ProjectOpened, *common_args)
        background_action_control.start(app_settings, ResolveStatus.ProjectOpened, *common_args)

        assert action_control.action.start_count == 0
        assert background_action_control.action.start_count == 0

        action_control.start(app_settings, ResolveStatus.TimelineOpened, *common_args)
        background_action_control.start(app_settings, ResolveStatus.TimelineOpened, *common_args)

        assert action_control.action.start_count == 1
        assert background_action_control.action.start_count == 1

    def test_validate_input(self, app_settings, resolve_app):
        action_control = ActionControl(MyAction())
        common_args = (app_settings, ResolveStatus.TimelineOpened, resolve_app, self.dummy_timeline_context)

        action_control.start(*common_args, input_data={"text": None})
        assert action_control.action.last_input_data == None

        action_control.start(*common_args, input_data={"text": "abc"})
        assert action_control.action.last_input_data == MyInput(text="abc")

    def test_update_action(self, app_settings, resolve_app):
        action_control = ActionControl(MyAction())
        common_start_args = (app_settings, ResolveStatus.TimelineOpened, resolve_app, self.dummy_timeline_context)
        common_update_args = (ResolveStatus.TimelineOpened, resolve_app, self.dummy_timeline_context, None)

        action_control.start(*common_start_args, input_data={"text": None})
        action_control.update(*common_update_args)
        assert action_control.input_data == None
        assert action_control.action.update_count == 0

        action_control.start(*common_start_args, input_data={"text": "abc"})
        action_control.update(*common_update_args)
        assert action_control.input_data == None
        assert action_control.action.update_count == 0

    def test_update_background_action(self, app_settings, resolve_app):
        background_action_control = ActionControl(MyBackgroundAction())
        common_start_args = (app_settings, ResolveStatus.TimelineOpened, resolve_app, self.dummy_timeline_context)
        common_update_args = (ResolveStatus.TimelineOpened, resolve_app, self.dummy_timeline_context, None)

        background_action_control.start(*common_start_args, input_data={"text": None})
        background_action_control.update(*common_update_args)
        assert background_action_control.input_data == MyInput()  # background action has default input
        assert background_action_control.action.update_count == 1

        background_action_control.start(*common_start_args, input_data={"text": "abc"})
        background_action_control.update(*common_update_args)
        assert background_action_control.input_data == MyInput(text="abc")
        assert background_action_control.action.update_count == 2
