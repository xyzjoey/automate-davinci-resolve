# import asyncio

from .context import AppContext, InputContext
from .actions import (
    auto_textplus_style,
    export_textplus,
    import_textplus,
    print_clip_info,
    sync_textplus_style,
)
from .actions.action_control import ActionControl
from .settings import AppSettings
from ..davinci.context import TimelineDiff, ResolveContext
from ..davinci.enums import ResolveStatus
from ..davinci.resolve_app import ResolveApp
from ..utils import log

from ..utils.timer import Timer


class App:
    action_types = [
        auto_textplus_style.Action,
        sync_textplus_style.Action,
        import_textplus.Action,
        export_textplus.Action,
        print_clip_info.Action,
    ]

    def __init__(self, resolve_app: ResolveApp):
        self.settings = AppSettings()
        self.resolve_app = resolve_app
        self.context = AppContext(
            resolve_context=ResolveContext(
                resolve_status=ResolveStatus.Unavailable,
                timeline_context=None,
                timeline_diff=None,
            )
        )

        self.actions = [ActionControl(action_type()) for action_type in self.action_types]

        self.load_resolve_cooldown = Timer()

    def apply_inputs(self, action_name, input_data: dict):
        action = self.get_action(action_name)

        if action is not None:
            action.apply_inputs(self.context.resolve_context.resolve_status, input_data)

    def update(self):
        resolve_context = self.load_resolve_context(force_load=False)
        self.context = AppContext(resolve_context)
        InputContext.set(InputContext(self.context.resolve_context.timeline_context))

        for action in self.actions:
            action.update(
                app_settings=self.settings,
                resolve_status=self.context.resolve_context.resolve_status,
                resolve_app=self.resolve_app,
                timeline_context=self.context.resolve_context.timeline_context,
                timeline_diff=self.context.resolve_context.timeline_diff,
            )

        return self.context

    def start_action(self, name, input_data: dict):
        action = self.get_action(name)

        if action is None:
            return

        resolve_context = self.load_resolve_context(force_load=True)
        self.context = AppContext(resolve_context)
        InputContext.set(InputContext(self.context.resolve_context.timeline_context))

        action.start(
            app_settings=self.settings,
            resolve_status=self.context.resolve_context.resolve_status,
            resolve_app=self.resolve_app,
            timeline_context=self.context.resolve_context.timeline_context,
            input_data=input_data,
        )

    def stop_action(self, name):
        action = self.get_action(name)

        if action is not None:
            action.stop()

    def get_action(self, name):
        return next((action for action in self.actions if action.name == name), None)

    def load_resolve_context(self, force_load: bool):
        if not force_load and not self.load_resolve_cooldown.expired():
            return ResolveContext(ResolveStatus.Unavailable, None, None)

        try:
            if self.context.resolve_context.resolve_status == ResolveStatus.Unavailable:
                log.info("Loading Resolve App...")
                log.flush()

            status = self.resolve_app.update()

            if status == ResolveStatus.Unavailable or status != self.context.resolve_context.resolve_status:
                log.info(f"Resolve status: {self.context.resolve_context.resolve_status.name} => {status.name}")

            if status == ResolveStatus.Unavailable and not force_load:
                log.warning("Failed to load Resolve App. Please check if Davinci Resolve is started and settings are correct. Will retry after 10s")
                self.load_resolve_cooldown.reset(10)

            if status != ResolveStatus.Unavailable:
                self.load_resolve_cooldown.reset(0)

            timeline_context = None
            timeline_diff = None

            if status == ResolveStatus.TimelineOpen:
                timeline_context = self.resolve_app.get_current_timeline().capture_context()
                timeline_diff = TimelineDiff.create(self.context.resolve_context.timeline_context, timeline_context)

            return ResolveContext(status, timeline_context, timeline_diff)

        except Exception as e:
            log.exception(e)
            log.error(f"Error when loading Resolve App. Will reload soon.")
            log.info(f"Resolve status: {self.context.resolve_context.resolve_status.name} => {ResolveStatus.Unavailable.name}")

            return ResolveContext(ResolveStatus.Unavailable, None, None)
