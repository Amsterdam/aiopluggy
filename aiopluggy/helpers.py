import inspect
import warnings


def varnames(func):
    """Return tuple of positional and keywrord argument names for a function,
    method, class or callable.

    In case of a class, its ``__init__`` method is considered.
    For methods the ``self`` parameter is not included.
    """
    spec = inspect.getfullargspec(func)
    # if spec.varargs or spec.varkw:
    #     raise Exception(
    #         "%s: Variable (keyword) arguments not allowed in hooks." %
    #         format_def(func)
    #     )
    args, defaults = tuple(spec.args), spec.defaults
    if defaults:
        index = -len(defaults)
        args, defaults = args[:index], tuple(args[index:])
    else:
        defaults = ()

    # strip any implicit instance arg
    if not inspect.isfunction(func) and not inspect.isbuiltin(func) and (
        inspect.ismethod(func) or inspect.isclass(func) or callable(func)
    ):
        if args[0] not in ('self', 'cls'):
            warnings.warn(
                "%s: expected first argument to be called 'self' or 'cls'. "
                "Found '%s' instead." % (
                    format_def(func), args[0]
                )
            )
        args = args[1:]

    return args, defaults


def format_def(func):
    return "%s%s" % (
        func.__name__,
        str(inspect.signature(func))
    )


class PluginValidationError(Exception):
    """ Plugin failed validation.
    """


def get_canonical_name(thing):
    """ Return canonical name for a plugin object.
    """
    return getattr(thing, "__name__", None) or str(id(thing))

