import pytest

from aiopluggy import *


hookspec = HookspecMarker("example")
hookimpl = HookimplMarker("example")


# noinspection PyStatementEffect
def test_spec_qualifiers():
    hookspec.first_result
    hookspec.replay
    hookspec.reraise
    hookspec.sync
    with pytest.raises(AttributeError):
        # noinspection PyUnresolvedReferences
        hookspec.non_existing


# noinspection PyStatementEffect
def test_impl_qualifiers():
    hookimpl.try_first
    hookimpl.try_last
    hookimpl.dont_await
    hookimpl.before
    with pytest.raises(AttributeError):
        # noinspection PyUnresolvedReferences
        hookimpl.non_existing
