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
def mock_resolve(monkeypatch, mock_resolve_data):
    with monkeypatch.context() as m:
        m.setattr("DaVinciResolveScript.scriptapp", lambda _: resolve_mock.ResolveAppMock(mock_resolve_data))
        yield
