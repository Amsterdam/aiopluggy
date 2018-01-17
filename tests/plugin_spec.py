from aiopluggy import HookspecMarker


hookspec = HookspecMarker("example")


@hookspec
def function_spec(arg1, arg2, foo='bar'):
    pass
