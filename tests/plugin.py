from aiopluggy import HookimplMarker


hookimpl = HookimplMarker("example")


@hookimpl
def function_impl(arg1, arg2, foo='bar'):
    pass


@hookimpl
class class1_impl(object):
    def __init__(self, arg1, arg2, foo='bar'):
        pass


class class2_impl(object):
    @hookimpl
    def __init__(self, arg1, arg2, foo='bar'):
        pass
