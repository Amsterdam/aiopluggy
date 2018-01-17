from aiopluggy import helpers

import plugin


def test_format_def():
    # noinspection PyUnusedLocal
    def my_func(a, b, c='d'):
        pass
    assert helpers.format_def(my_func) == 'my_func(a, b, c=\'d\')'


def test_fqn():
    klass = plugin.class1_impl
    assert helpers.fqn(klass) == 'plugin.class1_impl'
