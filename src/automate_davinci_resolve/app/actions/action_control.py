from contextlib import contextmanager
from enum import Enum
from typing import Optional

from pydantic import ValidationError

from .action_base import ActionBase
from .action_status import ActionStatus
from ..settings import AppSettings
from ...davinci.context import TimelineContext, TimelineDiff
from ...davinci.enums import ResolveStatus
from ...davinci.resolve_app import ResolveApp
from ...utils import log
from ...utils.timer import Timer
from ... import utils


class StatusControlResult(Enum):
    Changed = 0
    Unchanged = 1
    Failed = 2


class ActionStatusControl:
    def __init__(self, target_status: ActionStatus):
        self.status = ActionStatus.Stopped
        self.target_status = target_status

    def is_started(self):
        return self.status == ActionStatus.Started

    def should_start(self):
        return self.target_status == ActionStatus.Started

    def start(self):
        if self.target_status == ActionStatus.Started:
            return StatusControlResult.Unchanged
        elif self.target_status == ActionStatus.Stopped:
            self.target_status = ActionStatus.Started
            return StatusControlResult.Changed
        else:
            return StatusControlResult.Failed

    def stop(self):
        if self.target_status == ActionStatus.Started:
            self.target_status = ActionStatus.Stopped
            self.status = ActionStatus.Stopped
            return StatusControlResult.Changed
        else:
            return StatusControlResult.Unchanged

    def disable(self):
        self.target_status = ActionStatus.Disabled
        self.status = ActionStatus.Disabled

    def on_aciton_start(self):
        self.status = ActionStatus.Started

    def on_aciton_stop(self):
        self.status = ActionStatus.Stopped


class ActionControl:
    def __init__(self, action: ActionBase):
        self.action = action
        self.input_data = None
        self.run_in_background = hasattr(self.action, "update")
        self.status_control = ActionStatusControl(target_status=(ActionStatus.Started if self.run_in_background else ActionStatus.Stopped))

        self.error_count = 0
        self.error_timer = Timer()

    @property
    def action_type(self):
        return type(self.action)

    @property
    def name(self):
        return self.action.name

    @property
    def display_name(self):
        return self.action.display_name

    @property
    def description(self):
        return self.action.description

    @property
    def input_model(self):
        return self.action.input_model

    @property
    def is_starting(self):
        return self.status_control.should_start()

    def _parse_input(self, input_data: dict):
        validated_input_data = None

        try:
            validated_input_data = self.action.input_model.parse_obj(input_data)
        except ValidationError as e:
            log.exception(e)
            log.error(f"[{self.action}] Invalid input: {e}")

        return validated_input_data

    def apply_inputs(self, resolve_status: ResolveStatus, input_data: dict):
        if not self.run_in_background:
            return

        can_run = resolve_status.value >= self.action.required_status.value

        if can_run:
            validated_input_data = self._parse_input(input_data)

            if validated_input_data is not None:
                self.input_data = validated_input_data

    def update(
        self,
        app_settings: AppSettings,
        resolve_status: ResolveStatus,
        resolve_app: ResolveApp,
        timeline_context: Optional[TimelineContext],
        timeline_diff: Optional[TimelineDiff],
    ):
        if not self.run_in_background:
            return

        if self.input_data is None:
            self.input_data = self.input_model()

        for field_name, field_data in self.input_data:
            if hasattr(field_data, "update"):
                utils.forward_partial_args(field_data.update)(
                    timeline_context=timeline_context,
                    timeline_diff=timeline_diff,
                )

        if not self.status_control.should_start():
            return

        can_run = resolve_status.value >= self.action.required_status.value

        if not self.status_control.is_started() and can_run:
            log.info(f"[{self.action}] Resolve App enters required status. Start action now.")
        elif self.status_control.is_started() and not can_run:
            log.info(f"[{self.action}] Resolve App exits required status. Stop action now.")
            self.status_control.on_aciton_stop()

        if can_run:
            with self.on_try_action():
                utils.forward_partial_args(self.action.update)(
                    app_settings=app_settings,
                    resolve_app=resolve_app,
                    timeline_context=timeline_context,
                    timeline_diff=timeline_diff,
                    input_data=self.input_data,
                )

    def start(
        self,
        app_settings: AppSettings,
        resolve_status: ResolveStatus,
        resolve_app: ResolveApp,
        timeline_context: Optional[TimelineContext],
        input_data: dict,
    ):
        if self.status_control.start() == StatusControlResult.Failed:
            return

        if resolve_status.value < self.action.required_status.value:
            if not self.run_in_background:
                log.error(f"[{self.action}] Resolve App is not in ready status (expected={self.action.required_status.name})")
            else:
                log.warning(f"[{self.action}] Resolve App is not in ready status (expected={self.action.required_status.name}). Will retry after 10s")

            return

        if not hasattr(self.action, "start"):
            if not self.run_in_background:
                self.status_control.stop()

            return

        validated_input_data = self._parse_input(input_data)

        if validated_input_data is None:
            return

        if self.run_in_background:
            self.input_data = validated_input_data

        log.info(f"[{self.action}] Start action")
        log.flush()

        with self.on_try_action():
            utils.forward_partial_args(self.action.start)(
                app_settings=app_settings,
                resolve_app=resolve_app,
                timeline_context=timeline_context,
                input_data=validated_input_data,
            )

        if not self.run_in_background:
            self.status_control.stop()

    def stop(self):
        if self.status_control.stop() == StatusControlResult.Changed:
            log.info(f"[{self.action}] Stop action")

    @contextmanager
    def on_try_action(self):
        if self.error_timer.expired():
            self.error_count = 0

        self.error_timer.reset(5)

        try:
            self.status_control.on_aciton_start()
            yield
        except Exception as e:
            log.exception(e)
            log.error(f"[{self.action}] Error during action.")

            self.status_control.on_aciton_stop()

            self.error_count += 1

            if self.error_count > 5:
                log.critical(f"[{self.action}] Error tolerance exceeded (error count > 5). Disable action.")
                self.status_control.disable()
