import sys


class DummyModule:
    pass


def pytest_configure(config):
    sys.modules["DaVinciResolveScript"] = DummyModule

    config.pluginmanager.import_plugin("tests.plugin")
