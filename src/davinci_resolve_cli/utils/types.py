import typing
from typing import Union

from pydantic import BaseModel
from pydantic.fields import UndefinedType


def is_union(_type):
    return typing.get_origin(_type) is Union


def is_optional(_type):
    return is_union(_type) and type(None) in typing.get_args(_type)


def get_union_underlying_types(_type):
    return typing.get_args(_type)


def get_pydantic_field_default(model: BaseModel, field_name: str):
    field_info = model.__fields__[field_name].field_info
    default = field_info.default

    if isinstance(default, UndefinedType):
        return None

    return default
