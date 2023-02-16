import typing
from typing import Union


def is_optional(_type):
    return typing.get_origin(_type) is Union and type(None) in typing.get_args(_type)


def get_optional_underlying_type(_type):
    return typing.get_args(_type)[0]
