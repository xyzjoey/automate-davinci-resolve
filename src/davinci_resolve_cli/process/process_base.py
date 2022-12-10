import asyncio
from enum import Enum
import inspect
from typing import Type

from pydantic import BaseSettings

from ..davinci.resolve_context import ResolveContext, ResolveStatus
from ..inputs.argument_parser import ArgumentAndEnvParser
from ..utils import terminal_io
from ..utils.errors import CancelledError
from ..utils.settings import Settings


class ProcessResult(Enum):
    Done = 0
    Continue = 1


class ProcessBase:
    def __init__(self, input_model: Type[BaseSettings], required_resolve_status: ResolveStatus = ResolveStatus.TimelineAvail):
        self.settings = Settings.get()
        self.resolve_context = ResolveContext.get()
        self.input_model = input_model
        self.required_resolve_status = required_resolve_status

        self.resolve_context.update()

    async def run(self):
        while True:
            status = self.resolve_context.update()

            if status.value < self.required_resolve_status.value:
                if status == ResolveStatus.NotAvail:
                    terminal_io.print_error("Failed to load Davinci Resolve script app. Is Davinci Resolve running?")
                    return
                elif status == ResolveStatus.ProjectManagerAvail:
                    terminal_io.print_error("Davinci Resolve project is not opened")
                    return
                elif status == ResolveStatus.ProjectAvail:
                    terminal_io.print_error("Davinci Resolve timeline is not opened")
                    return

            inputs = None

            try:
                inputs = self.get_inputs()
            except CancelledError:
                terminal_io.print_warning("Cancelled")
                return

            if inspect.iscoroutinefunction(self.run_with_input):
                result = await self.run_with_input(inputs)
            else:
                result = self.run_with_input(inputs)

            if result == ProcessResult.Done:
                return

    def get_inputs(self):
        parser = ArgumentAndEnvParser(self.input_model)
        return parser.parse_args_and_env()

    def main(self):
        asyncio.run(self.run())
