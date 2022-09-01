import asyncio
from enum import Enum
from typing import Type

from pydantic import BaseSettings

from ..davinci.resolve_context import ResolveContext, ResolveStatus
from ..inputs.argument_parser import ArgumentAndEnvParser
from ..utils import terminal_io
from ..utils.errors import CancelledError


class ProcessResult(Enum):
    Done = 0
    Continue = 1


class ProcessBase:
    def __init__(self, input_model: Type[BaseSettings]):
        self.resolve_context = ResolveContext.get()
        self.input_model = input_model

    async def run(self, use_arg_parser=False):
        while True:
            status = self.resolve_context.update()

            if status == ResolveStatus.NotAvail:
                terminal_io.print_error("Failed to load Davinci Resolve script app. Is Davinci Resolve running?")
                return
            elif status == ResolveStatus.ProjectAvail:
                terminal_io.print_error("Davinci Resolve project is not opened")
                return

            inputs = None

            try:
                inputs = self.get_inputs(use_arg_parser)
            except CancelledError:
                terminal_io.print_warning("Cancelled")
                return

            result = await self.run_with_input(inputs)

            if result == ProcessResult.Done:
                return


    def get_inputs(self, use_arg_parser):
        if use_arg_parser:
            parser = ArgumentAndEnvParser(self.input_model)
            return parser.parse_args_and_env()
        else:
            return self.input_model()

    def main(self):
        asyncio.run(self.run(use_arg_parser=True))
