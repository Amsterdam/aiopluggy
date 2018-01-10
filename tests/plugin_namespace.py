from aiopluggy import *


hookspec = HookspecMarker("example")
hookimpl = HookimplMarker("example")


@hookspec
def function_spec(arg1, arg2):
    pass


@hookimpl
def function_impl(arg1, arg2):
    pass


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
