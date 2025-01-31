import pytest

from automate_davinci_resolve.app.app import App
from automate_davinci_resolve.app.context import InputContext
from automate_davinci_resolve.gui.app import GuiApp

from .utils.resolve_mock import ResolveAppMock
from .utils.settings import TestSettings


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
