import pytest

from aiopluggy import *


hookspec = HookspecMarker("example")
hookimpl = HookimplMarker("example")


# noinspection PyStatementEffect
def test_spec_qualifiers():
    hookspec.first_notnone
    hookspec.first_only
    hookspec.replay
    hookspec.sync
    hookspec.required
    with pytest.raises(AttributeError):
        # noinspection PyUnresolvedReferences
        hookspec.non_existing
    with pytest.raises(AttributeError):
        hookspec.first_notnone.first_only


# noinspection PyStatementEffect
def test_impl_qualifiers():
    hookimpl.try_first
    hookimpl.try_last
    hookimpl.dont_await
    hookimpl.before
    with pytest.raises(AttributeError):
        # noinspection PyUnresolvedReferences
        hookimpl.non_existing
