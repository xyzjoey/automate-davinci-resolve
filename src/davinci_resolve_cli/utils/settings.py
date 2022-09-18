from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    data_dir: Path
    temp_dir: Path

    _settings: "Settings" = None

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.temp_dir.mkdir(exist_ok=True)

    @classmethod
    def get(cls):
        if cls._settings is None:
            cls._settings = Settings()

        return cls._settings
