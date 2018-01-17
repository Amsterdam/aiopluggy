from aiopluggy import helpers

import plugin


def test_fqn():
    klass = plugin.class1_impl
    assert helpers.fqn(klass) == 'plugin.class1_impl'
