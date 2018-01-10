from aiopluggy import *


hookspec = HookspecMarker("example")
hookimpl = HookimplMarker("example")


@hookspec
def function_spec(arg1, arg2):
    pass


class _C(object):
    @hookspec
    def __call__(self, arg1, arg2):
        pass


callable_spec = _C()


@hookspec
class class1_spec(object):
    def __init__(self, arg1, arg2):
        pass


class class2_spec(object):
    @hookspec
    def __init__(self, arg1, arg2):
        pass


@hookimpl
def function_impl(arg1, arg2):
    pass


class _C(object):
    @hookimpl
    def __call__(self, arg1, arg2):
        pass


callable_impl = _C()


@hookimpl
class class1_impl(object):
    def __init__(self, arg1, arg2):
        pass


class class2_impl(object):
    @hookimpl
    def __init__(self, arg1, arg2):
        pass


def example_plugin_impl(arg1, arg2):
    pass
