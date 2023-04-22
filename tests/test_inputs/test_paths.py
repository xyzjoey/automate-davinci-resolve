from pathlib import Path

from pydantic import BaseModel, ValidationError

from automate_davinci_resolve.app.inputs.paths import SaveFilePathInput


class Input(BaseModel):
    path: SaveFilePathInput


class TestSaveFilePathInput:
    def test_valid_input(self, app_settings):
        path = Input(path=f"{app_settings.temp_dir}/abc.txt").path

        assert path == Path(f"{app_settings.temp_dir}/abc.txt")

    def test_invalid_input(self, app_settings):
        try:
            path = Input(path=f"{app_settings.temp_dir}").path
            assert False
        except ValidationError:
            assert True
