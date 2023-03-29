from pathlib import Path

from pydantic import BaseSettings


class TestSettings(BaseSettings):
    resource_dir: Path
