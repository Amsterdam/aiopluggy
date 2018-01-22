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


class Result(object):
    def __init__(self, value=None, exc_info=None):
        assert exc_info is None or exc_info[1] is not None
        self._value = value
        self._exc_info = exc_info

    @property
    def value(self):
        """Get the result(s) for this hook call.

        If the hook was marked as a :ref:`tutorial:first_notnone` or
        :ref:`tutorial:first_only` only a single value will be returned
        otherwise a list of results.

        """
        # __tracebackhide__ = True
        if self._exc_info is None:
            return self._value
        else:
            ex = self._exc_info
            raise ex[1].with_traceback(ex[2])

    @value.setter
    def value(self, value):
        self._exc_info = None
        self._value = value

    @property
    def exc_info(self):
        """Exception info.

        :rtype: a tuple. See :func:`sys.exc_info` for details.

        """
        return self._exc_info

    @property
    def exception(self):
        """Exception info.

        :rtype: a tuple. See :func:`sys.exc_info` for details.

        """
        return self._exc_info[1] if self._exc_info else None
