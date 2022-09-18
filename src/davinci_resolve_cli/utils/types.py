from typing import Type

from pydantic import BaseSettings


def create_optional_model(model: Type[BaseSettings], default_value):
    optional_model = type(f"Optional{model.__name__}", (model,), {})

    for field in optional_model.__fields__.values():
        field.default = default_value
        field.default_factory = None
        field.required = False

    return optional_model


def create_env_getter(model: Type[BaseSettings], env_file):
    env_getter_cls = type(f"{model.__name__}EnvGetter", (model,), {
        "__init__": lambda _: None,
        "get": lambda self: self._build_values({}, _env_file=env_file)
    })

    return env_getter_cls()
