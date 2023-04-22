from pathlib import Path

from pydantic import BaseModel


class _Path(BaseModel):
    path: Path


class SaveFilePathInput(type(Path())):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        # TODO use Validator on pydantic v2 available
        # https://github.com/pydantic/pydantic/blob/main/docs/blog/pydantic-v2.md#validation-without-a-model-thumbsup
        path = _Path(path=v).path
        path = path.resolve()

        if path.is_dir():
            raise ValueError(f"{path.name} is a directory")

        return cls(path)
