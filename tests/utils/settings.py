from pathlib import Path

from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    resource_dir: Path
