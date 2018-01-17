import inspect


def fqn(namespace) -> str:
    """ Return fully qualified name of ``thing``.

    :param namespace: must be a module, class, or instance.
    :rtype: str

    """
    if inspect.ismodule(namespace):
        return namespace.__name__
    elif inspect.isclass(namespace):
        return namespace.__module__ + '.' + namespace.__qualname__
    try:
        # namespace should be an instance.
        klass = namespace.__class__
        return '%s.%s(%s)' % (klass.__module__, klass.__qualname__, id(namespace))
    except AttributeError:
        raise TypeError("Argument must be a module, class, or instance.") from None
