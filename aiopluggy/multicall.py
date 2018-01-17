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


async def _call_befores(hookimpls, caller_kwargs):
    awaitables = []
    # noinspection PyBroadException
    try:  # <-- to cancel any unfinished awaitables
        for hookimpl in reversed(hookimpls):
            kwargs = hookimpl.filtered_args(caller_kwargs)
            if hookimpl.is_async:
                awaitables.append(asyncio.ensure_future(
                    hookimpl.function(**kwargs)
                ))
            else:
                hookimpl.function(**kwargs)
        if len(awaitables) > 0:
            for f in asyncio.as_completed(awaitables):
                await f
    except Exception:
        for a in awaitables:
            if not a.done():
                a.cancel()
        raise


def _call_befores_sync(hookimpls, caller_kwargs):
    # noinspection PyBroadException
    for hookimpl in reversed(hookimpls):
        kwargs = hookimpl.filtered_args(caller_kwargs)
        hookimpl.function(**kwargs)


async def multicall_parallel(before, functions, caller_kwargs, reraise):
    """Execute a call into multiple python methods.

    ``caller_kwargs`` comes from HookCaller.__call__().

    """
    # __tracebackhide__ = True
    await _call_befores(before, caller_kwargs=caller_kwargs)
    awaitables = []
    # noinspection PyBroadException
    try:  # <-- to cancel any unfinished awaitables
        for hookimpl in reversed(functions):
            kwargs = hookimpl.filtered_args(caller_kwargs)
            if hookimpl.is_async:
                awaitables.append(asyncio.ensure_future(
                    hookimpl.function(**kwargs)
                ))
            elif reraise:
                yield hookimpl.function(**kwargs)
            else:
                # noinspection PyBroadException
                try:
                    yield Result(hookimpl.function(**kwargs))
                except Exception:
                    yield Result(exc_info=sys.exc_info())
        if len(awaitables) > 0:
            for f in asyncio.as_completed(awaitables):
                if reraise:
                    yield await f
                else:
                    # noinspection PyBroadException
                    try:
                        yield Result(await f)
                    except Exception:
                        yield Result(exc_info=sys.exc_info())
    except Exception:
        for a in awaitables:
            if not a.done():
                a.cancel()
        raise


def multicall_parallel_sync(before, functions, caller_kwargs, reraise):
    """Execute a call into multiple python methods.

    Called from :func:`HookCaller.__call__`.

    """
    # __tracebackhide__ = True
    _call_befores_sync(before, caller_kwargs=caller_kwargs)
    for hookimpl in reversed(functions):
        kwargs = hookimpl.filtered_args(caller_kwargs)
        if reraise:
            yield hookimpl.function(**kwargs)
        else:
            # noinspection PyBroadException
            try:
                yield Result(hookimpl.function(**kwargs))
            except Exception:
                yield Result(exc_info=sys.exc_info())


async def multicall_first(before, functions, caller_kwargs, reraise):
    """Execute a call into multiple python methods.

    Called from :func:`HookCaller.__call__`.

    """
    # __tracebackhide__ = True
    assert reraise == True
    await _call_befores(before, caller_kwargs=caller_kwargs)
    for hookimpl in reversed(functions):
        kwargs = hookimpl.filtered_args(caller_kwargs)
        result = hookimpl.function(**kwargs)
        if hookimpl.is_async:
            result = await result
        if result is not None:
            return result
    return None


def multicall_first_sync(before, functions, caller_kwargs, reraise):
    """Execute a call into multiple python methods.

    Called from :func:`HookCaller.__call__`.

    """
    # __tracebackhide__ = True
    assert reraise == True
    _call_befores_sync(before, caller_kwargs=caller_kwargs)
    for hookimpl in reversed(functions):
        kwargs = hookimpl.filtered_args(caller_kwargs)
        result = hookimpl.function(**kwargs)
        if result is not None:
            return result
    return None
