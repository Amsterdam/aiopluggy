import asyncio
import pytest

from aiopluggy import *


hookspec = HookspecMarker("example")
hookimpl = HookimplMarker("example")


def test_spec_conflicting():
    with pytest.raises(AttributeError):
        hookspec.first_result.historic
    with pytest.raises(AttributeError):
        hookimpl.try_first.try_last
