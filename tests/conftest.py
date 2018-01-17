import pytest


@pytest.fixture
def pm():
    from aiopluggy import PluginManager
    return PluginManager('example')
