from pathlib import Path

from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    data_dir: Path  # use DirectoryPath?
    temp_dir: Path

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.temp_dir.mkdir(exist_ok=True)
