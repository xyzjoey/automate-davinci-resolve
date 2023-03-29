import pytest

from .utils.resolve_mock import ResolveAppMock
from .utils.settings import TestSettings
from davinci_resolve_cli.app.app import App
from davinci_resolve_cli.app.context import InputContext
from davinci_resolve_cli.gui.app import GuiApp


@pytest.fixture
def resolve_app():
    return ResolveAppMock()


@pytest.fixture
def app(resolve_app):
    return App(resolve_app)


@pytest.fixture
def gui_app(app):
    return GuiApp(app)  # FIXME cannot init multiple tk root


@pytest.fixture
def app_settings(app):
    return app.settings


@pytest.fixture
def test_settings():
    return TestSettings()


@pytest.fixture(autouse=True)
def clean():
    yield
    InputContext.set(None)
