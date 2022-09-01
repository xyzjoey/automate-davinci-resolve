import argparse

from pydantic import BaseSettings
import pytest

from davinci_resolve_cli.inputs.argument_parser import ArgumentAndEnvParser


class MyModel(BaseSettings):
    required_field: int
    optional_field: str = "abc"


class TestArgumentAndEnvParser:
    def test_parse_nothing(self):
        parser = ArgumentAndEnvParser(MyModel)

        with pytest.raises(argparse.ArgumentError):
            parser.parse_args_and_env([])

    def test_parse_args(self):
        parser = ArgumentAndEnvParser(MyModel)

        obj = parser.parse_args_and_env(["--required-field", "123"])

        assert obj.required_field == 123
        assert obj.optional_field == "abc"

        obj = parser.parse_args_and_env(["--required-field", "123", "--optional-field", "xyz"])

        assert obj.required_field == 123
        assert obj.optional_field == "xyz"

    def test_parse_env(self, tmp_path):
        env_file_path = tmp_path / ".env"
        env_file_path.write_text(
            """
            REQUIRED_FIELD=123
            OPTIONAL_FIELD=xyz
            """
        )

        parser = ArgumentAndEnvParser(MyModel, env_file=env_file_path)

        obj = parser.parse_args_and_env([])

        assert obj.required_field == 123
        assert obj.optional_field == "xyz"

    def test_parse_args_and_env(self, tmp_path):
        env_file_path = tmp_path / ".env"
        env_file_path.write_text(
            """
            REQUIRED_FIELD=123
            OPTIONAL_FIELD=xyz
            """
        )

        parser = ArgumentAndEnvParser(MyModel, env_file=env_file_path)

        obj = parser.parse_args_and_env(["--optional-field", "zzz"])

        assert obj.required_field == 123
        assert obj.optional_field == "zzz"
