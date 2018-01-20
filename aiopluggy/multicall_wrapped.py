""" Call loop machinery.
"""
import asyncio
import sys


def _raise_wrapfail(generator, msg):
    co = generator.gi_code
    raise RuntimeError(
        "wrap_controller at %r %s:%d %s" % (
            co.co_name, co.co_filename, co.co_firstlineno, msg
        )
    ) from None


class HookWrapperException(Exception):
    """ Wrapper for a set of exceptions raised during hook wrapper teardown.

    .. :py:attribute:: causes

        :type: List[Exception]

    """
    def __init__(self, causes, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.causes = causes


class Result(object):
    def __init__(self, value=None, exc_info=None):
        self._value = value
        self._exc_info = exc_info

    @property
    def value(self):
        """Get the result(s) for this hook call.

        If the hook was marked as a ``firstresult`` only a single value
        will be returned otherwise a list of results.
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


# noinspection PyBroadException
def multicall_parallel_wrapped(
    wrappers,
    implementations,
    caller_kwargs
):
    """Execute a call into multiple python methods.

    ``caller_kwargs`` comes from HookCaller.__call__().

    """
    # __tracebackhide__ = True
    teardowns = []
    try:  # <-- to protect all tear-down calls

        for wrapper in reversed(wrappers):
            kwargs = wrapper.filtered_args(caller_kwargs)
            if wrapper.is_async:
                try:
                    gen = wrapper.function(**kwargs)
                    yield from gen.__anext__()  # first yield
                    teardowns.append((True, gen))
                except StopAsyncIteration:
                    _raise_wrapfail(gen, "did not yield")
            else:
                try:
                    gen = wrapper.function(**kwargs)
                    next(gen)   # first yield
                    teardowns.append((False, gen))
                except StopIteration:
                    _raise_wrapfail(gen, "did not yield")

        awaitables = []
        try:  # <-- to cancel any unfinished awaitables
            for implementation in reversed(implementations):
                kwargs = implementation.filtered_args(caller_kwargs)
                if implementation.is_async:
                    awaitables.append(asyncio.ensure_future(
                        implementation.function(**kwargs)
                    ))
                else:
                    try:
                        yield Result(implementation.function(**kwargs))
                    except Exception:
                        yield Result(exc_info=sys.exc_info())
            if len(awaitables) > 0:
                for f in asyncio.as_completed(awaitables):
                    try:
                        result = yield from f
                        yield Result(result)
                    except Exception:
                        yield Result(exc_info=sys.exc_info())
        except Exception:
            for a in awaitables:
                if not a.done():
                    a.cancel()
            raise

    finally:
        # run all wrapper post-yield blocks
        causes = []
        for is_async, gen in reversed(teardowns):
            try:
                if is_async:
                    yield from gen.asend(result)
                else:
                    gen.send(result)
            except (StopAsyncIteration, StopIteration):
                pass
            except Exception as e:
                causes.append(e)
            else:
                _raise_wrapfail(gen, "has second yield")
        if len(causes) > 0:
            raise HookWrapperException(causes)


# noinspection PyBroadException
def multicall_parallel(implementations, caller_kwargs):
    """Execute a call into multiple python methods.

    ``caller_kwargs`` comes from HookCaller.__call__().

    """
    # __tracebackhide__ = True
    teardowns = []
    try:  # <-- to protect all tear-down calls

        for wrapper in reversed(wrappers):
            kwargs = wrapper.filtered_args(caller_kwargs)
            if wrapper.is_async:
                try:
                    gen = wrapper.function(**kwargs)
                    yield from gen.__anext__()  # first yield
                    teardowns.append((True, gen))
                except StopAsyncIteration:
                    _raise_wrapfail(gen, "did not yield")
            else:
                try:
                    gen = wrapper.function(**kwargs)
                    next(gen)   # first yield
                    teardowns.append((False, gen))
                except StopIteration:
                    _raise_wrapfail(gen, "did not yield")

        awaitables = []
        try:  # <-- to cancel any unfinished awaitables
            for implementation in reversed(implementations):
                kwargs = implementation.filtered_args(caller_kwargs)
                if implementation.is_async:
                    awaitables.append(asyncio.ensure_future(
                        implementation.function(**kwargs)
                    ))
                else:
                    try:
                        yield Result(implementation.function(**kwargs))
                    except Exception:
                        yield Result(exc_info=sys.exc_info())
            if len(awaitables) > 0:
                for f in asyncio.as_completed(awaitables):
                    try:
                        result = yield from f
                        yield Result(result)
                    except Exception:
                        yield Result(exc_info=sys.exc_info())
        except Exception:
            for a in awaitables:
                if not a.done():
                    a.cancel()
            raise

    finally:
        # run all wrapper post-yield blocks
        causes = []
        for is_async, gen in reversed(teardowns):
            try:
                if is_async:
                    yield from gen.asend(result)
                else:
                    gen.send(result)
            except (StopAsyncIteration, StopIteration):
                pass
            except Exception as e:
                causes.append(e)
            else:
                _raise_wrapfail(gen, "has second yield")
        if len(causes) > 0:
            raise HookWrapperException(causes)


# noinspection PyBroadException
def multicall_parallel_sync_wrapped(
    wrappers,
    implementations,
    caller_kwargs
):
    """Execute a call into multiple python methods.

    ``caller_kwargs`` comes from HookCaller.__call__().

    """
    # __tracebackhide__ = True
    teardowns = []
    try:  # <-- to protect all tear-down calls

        for wrapper in reversed(wrappers):
            kwargs = wrapper.filtered_args(caller_kwargs)
            gen = wrapper.function(**kwargs)
            try:
                next(gen)   # first yield
                teardowns.append((False, gen))
            except StopIteration:
                _raise_wrapfail(gen, "did not yield")

        for implementation in reversed(implementations):
            kwargs = implementation.filtered_args(caller_kwargs)
            try:
                yield Result(implementation.function(**kwargs))
            except Exception:
                yield Result(exc_info=sys.exc_info())

    finally:
        # run all wrapper post-yield blocks
        causes = []
        for is_async, gen in reversed(teardowns):
            try:
                gen.send()
            except StopIteration:
                pass
            except Exception as e:
                causes.append(e)
            else:
                _raise_wrapfail(gen, "has second yield")
        if len(causes) > 0:
            raise HookWrapperException(causes)


# noinspection PyBroadException
def multicall_parallel_sync(implementations, caller_kwargs):
    """Execute a call into multiple python methods.

    ``caller_kwargs`` comes from HookCaller.__call__().

    """
    # __tracebackhide__ = True

    for implementation in reversed(implementations):
        kwargs = implementation.filtered_args(caller_kwargs)
        try:
            yield Result(implementation.function(**kwargs))
        except Exception:
            yield Result(exc_info=sys.exc_info())


def multicall_first(wrappers, implementations, caller_kwargs):
    """Execute a call into multiple python methods.

    ``caller_kwargs`` comes from HookCaller.__call__().

    """
    # __tracebackhide__ = True
    result = None
    teardowns = []
    try:

        for wrapper in reversed(wrappers):
            kwargs = wrapper.filtered_args(caller_kwargs)
            if wrapper.is_async:
                try:
                    gen = wrapper.function(**kwargs)
                    yield from gen.__anext__()  # first yield
                    teardowns.append((True, gen))
                except StopAsyncIteration:
                    _raise_wrapfail(gen, "did not yield")
            else:
                try:
                    gen = wrapper.function(**kwargs)
                    next(gen)   # first yield
                    teardowns.append((False, gen))
                except StopIteration:
                    _raise_wrapfail(gen, "did not yield")

        for implementation in reversed(implementations):
            kwargs = implementation.filtered_args(caller_kwargs)
            result = implementation.function(**kwargs)
            if implementation.is_async:
                result = yield from result
            if result is not None:
                break
    finally:
        # run all wrapper post-yield blocks
        causes = []
        for is_async, gen in reversed(teardowns):
            try:
                if is_async:
                    yield from gen.asend(result)
                else:
                    gen.send(result)
            except (StopAsyncIteration, StopIteration):
                pass
            except Exception as e:
                causes.append(e)
            else:
                _raise_wrapfail(gen, "has second yield")
        if len(causes) > 0:
            raise HookWrapperException(causes)

    return result
