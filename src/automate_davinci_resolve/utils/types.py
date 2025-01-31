import typing
from typing import Union

from pydantic import BaseModel


def is_union(_type):
    return typing.get_origin(_type) is Union


def is_optional(_type):
    return is_union(_type) and type(None) in typing.get_args(_type)


def get_union_underlying_types(_type):
    return typing.get_args(_type)


def get_pydantic_field_default(model: BaseModel, field_name: str):
    field_info = model.model_fields[field_name]

    if field_info.is_required():
        return None
    else:
        return field_info.get_default()
