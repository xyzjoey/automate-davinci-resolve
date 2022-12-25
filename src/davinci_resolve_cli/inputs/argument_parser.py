import argparse
from typing import Type

from pydantic import BaseSettings, ValidationError
import pydantic_argparse

from ..utils import types


class ArgumentAndEnvParser(pydantic_argparse.ArgumentParser):
    def __init__(self, model: Type[BaseSettings], env_file=".env", *args, **kw):
        self.original_model = model
        self.optional_model = types.create_optional_model(model, default_value=argparse.SUPPRESS)
        self.env_getter = types.create_env_getter(model, env_file=env_file)

        kw["exit_on_error"] = False

        super().__init__(self.optional_model, *args, **kw)

    def parse_args_and_env(self, args=None):
        envs = self.env_getter.get()
        namespace = self.parse_args(args)

        parsed_args = {**envs, **namespace.__dict__}

        try:
            return self.original_model.parse_obj(parsed_args)
        except ValidationError as e:
            self.error(str(e))
