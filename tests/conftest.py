import sys

import pytest

from utils import resolve_mock


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "mock_resolve_current_timeline(data): mock current timeline data"
    )

    # mock module import
    sys.modules["DaVinciResolveScript"] = resolve_mock


@pytest.fixture
def mock_resolve_data(request):
    marker = request.node.get_closest_marker("mock_resolve_current_timeline")

    default_data = {
        "project_manager": {
            "current_project": {
                "media_pool": {},
                "current_timeline": {},
            }
        },
        "media_storage": {}
    }

    if marker is None or len(marker.args) == 0:
        return default_data

    default_data["project_manager"]["current_project"]["current_timeline"] = marker.args[0]

    return default_data


@pytest.fixture(autouse=True)
def resolve_app(monkeypatch, mock_resolve_data):
    with monkeypatch.context() as m:
        resolve_app_mock = resolve_mock.ResolveAppMock(mock_resolve_data)
        m.setattr("DaVinciResolveScript.scriptapp", lambda _: resolve_app_mock)
        yield resolve_app_mock


@pytest.fixture
def current_timeline(resolve_app: resolve_mock.ResolveAppMock):
    return resolve_app.GetProjectManager().GetCurrentProject().GetCurrentTimeline()
