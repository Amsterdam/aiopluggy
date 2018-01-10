""" Call loop machinery.
"""
import sys
import asyncio


def _raise_wrapfail(wrap_controller, msg):
    co = wrap_controller.gi_code
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


# noinspection PyBroadException
async def multicall_parallel(wrappers,
                             implementations,
                             caller_kwargs,
                             return_exceptions=False):
    """Execute a call into multiple python methods.

    ``caller_kwargs`` comes from HookCaller.__call__().

    """
    # __tracebackhide__ = True
    result = [None] * len(implementations)
    teardowns = []
    try:

        for wrapper in reversed(wrappers):
            args = wrapper.filtered_args(caller_kwargs)
            if wrapper.is_asyncio:
                try:
                    gen = wrapper.function(*args)
                    await gen.__anext__()  # first yield
                    teardowns.append((True, gen))
                except StopAsyncIteration:
                    _raise_wrapfail(gen, "did not yield")
            else:
                try:
                    gen = wrapper.function(*args)
                    next(gen)   # first yield
                    teardowns.append((False, gen))
                except StopIteration:
                    _raise_wrapfail(gen, "did not yield")

        awaitables = []
        current_index = 0
        for implementation in reversed(implementations):
            args = implementation.filtered_args(caller_kwargs)
            if implementation.is_asyncio:
                awaitables.append([
                    current_index,
                    implementation.function(*args)
                ])
            else:
                try:
                    res = implementation.function(*args)
                except BaseException:
                    if not return_exceptions:
                        raise
                    result[current_index] = Result(exc_info=sys.exc_info())
                else:
                    result[current_index] = Result(res)
            current_index += 1
        if len(awaitables) > 0:
            try:
                coros = [a[1] for a in awaitables]
                gathered = await asyncio.gather(
                    *coros,
                    return_exceptions=return_exceptions
                )
            except BaseException as e:
                print(repr(e))
                raise
            for i in range(len(gathered)):
                res = gathered[i]
                result_index = awaitables[i][0]
                result[result_index] = (
                    Result(exc_info=(res.__class__, res, None))
                    if return_exceptions and isinstance(res, BaseException)
                    else Result(res)
                )

    finally:

        # run all wrapper post-yield blocks
        for is_asyncio, gen in reversed(teardowns):
            if is_asyncio:
                try:
                    await gen.asend(result)
                    _raise_wrapfail(gen, "has second yield")
                except StopAsyncIteration:
                    pass
            else:
                try:
                    gen.send(result)
                    _raise_wrapfail(gen, "has second yield")
                except StopIteration:
                    pass

    return result


async def multicall_first(wrappers, implementations, caller_kwargs):
    """Execute a call into multiple python methods.

    ``caller_kwargs`` comes from HookCaller.__call__().

    """
    # __tracebackhide__ = True
    result = None
    teardowns = []
    try:

        for wrapper in reversed(wrappers):
            args = wrapper.filtered_args(caller_kwargs)
            if wrapper.is_asyncio:
                try:
                    gen = wrapper.function(*args)
                    await gen.__anext__()  # first yield
                    teardowns.append((True, gen))
                except StopAsyncIteration:
                    _raise_wrapfail(gen, "did not yield")
            else:
                try:
                    gen = wrapper.function(*args)
                    next(gen)   # first yield
                    teardowns.append((False, gen))
                except StopIteration:
                    _raise_wrapfail(gen, "did not yield")

        for implementation in reversed(implementations):
            args = implementation.filtered_args(caller_kwargs)
            result = implementation.function(*args)
            if implementation.is_asyncio:
                result = await result
            if result is not None:
                break
    finally:

        # run all wrapper post-yield blocks
        for is_asyncio, gen in reversed(teardowns):
            if is_asyncio:
                try:
                    await gen.asend(result)
                    _raise_wrapfail(gen, "has second yield")
                except StopAsyncIteration:
                    pass
            else:
                try:
                    gen.send(result)
                    _raise_wrapfail(gen, "has second yield")
                except StopIteration:
                    pass

    return result
