import asyncio
import weakref

import sys

from .hooks import HookSpec
from .helpers import Result


def _priority_groups(hookimpls):
    result = [[], [], []]
    for h in hookimpls:
        if h.is_try_first:
            result[0].append(h)
        elif not h.is_try_last:
            result[1].append(h)
        else:
            result[2].append(h)
    return result


class HookCaller(object):
    def __init__(self, name, plugin_manager):
        self.name = name
        """:type: str"""
        self._plugin_manager = weakref.ref(plugin_manager)
        self.before = []
        """:type: list[aiopluggy.hooks.HookImpl]"""
        self.functions = []
        """:type: list[aiopluggy.hooks.HookImpl]"""
        self.spec = None
        """:type: aiopluggy.hooks.HookSpec"""

    @property
    def plugin_manager(self):
        """:rtype: aiopluggy.PluginManager"""
        return self._plugin_manager()

    def set_spec(self, namespace, flag_set):
        assert self.spec is None
        self.spec = HookSpec(namespace, self.name, flag_set)
        for hookimpl in (self.before + self.functions):
            hookimpl.validate_against(self.spec)

    def add_hookimpl(self, hookimpl):
        """A an implementation to the callback chain.
        """
        if self.spec:
            hookimpl.validate_against(self.spec)

        if hookimpl.is_before:
            methods = self.before
        else:
            methods = self.functions

        if hookimpl.is_try_last:
            methods.insert(0, hookimpl)
        elif hookimpl.is_try_first:
            methods.append(hookimpl)
        else:
            # find last non-try_first method
            i = len(methods) - 1
            while i >= 0 and methods[i].is_try_first:
                i -= 1
            methods.insert(i + 1, hookimpl)

    def __repr__(self):
        return "<HookCaller %r>" % (self.name,)

    def __call__(self, *args, **kwargs):
        if args:
            raise TypeError("hook calling supports only keyword arguments")
        multicall_ = self._multicall_parallel_sync if self.spec.is_sync else self._multicall_parallel
        if self.spec is None:
            return multicall_(
                before=self.before,
                functions=self.functions,
                caller_kwargs=kwargs,
                reraise=False
            )
        notinspec = set(kwargs.keys()) - self.spec.req_args - set(self.spec.opt_args.keys())
        if notinspec:
            raise TypeError(
                # TODO: show spec signature
                "Argument(s) %s not declared in hookspec" % (notinspec,),
            )
        notincall = self.spec.req_args - set(kwargs.keys())
        if notincall:
            raise TypeError(
                # TODO: show spec signature
                "Missing required argument(s): %s" % (notincall,)
            )
        if self.spec.is_replay:
            self.plugin_manager.history.append((self.name, kwargs))
        if self.spec.is_first_result:
            multicall_ = self._multicall_first_sync if self.spec.is_sync else self._multicall_first
        return multicall_(
            caller_kwargs=kwargs,
            reraise=self.spec.is_reraise
        )

    async def _call_befores(self, caller_kwargs):
        async def call_befores(hookimpl_group):
            awaitables = []
            # noinspection PyBroadException
            try:  # <-- to cancel any unfinished awaitables
                for hookimpl in reversed(hookimpl_group):
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

        for group in _priority_groups(self.before):
            await call_befores(group)

    def _call_befores_sync(self, caller_kwargs):
        # noinspection PyBroadException
        for hookimpl in reversed(self.before):
            kwargs = hookimpl.filtered_args(caller_kwargs)
            hookimpl.function(**kwargs)

    async def _multicall_parallel(self, caller_kwargs, reraise, functions=None):
        """Execute a call into multiple python methods.

        ``caller_kwargs`` comes from HookCaller.__call__().

        """
        # __tracebackhide__ = True
        if functions is None:
            functions = self.functions
        await self.plugin_manager.await_unscheduled_coros()
        await self._call_befores(caller_kwargs=caller_kwargs)
        retval = []

        async def multicall_parallel(hookimpl_group):
            awaitables = []
            # noinspection PyBroadException
            try:  # <-- to cancel any unfinished awaitables
                for hookimpl in reversed(hookimpl_group):
                    kwargs = hookimpl.filtered_args(caller_kwargs)
                    if hookimpl.is_async:
                        awaitables.append(asyncio.ensure_future(
                            hookimpl.function(**kwargs)
                        ))
                    elif reraise:
                        retval.append(hookimpl.function(**kwargs))
                    else:
                        # noinspection PyBroadException
                        try:
                            retval.append(Result(hookimpl.function(**kwargs)))
                        except Exception:
                            retval.append(Result(exc_info=sys.exc_info()))
                if len(awaitables) > 0:
                    for f in asyncio.as_completed(awaitables):
                        if reraise:
                            retval.append(await f)
                        else:
                            # noinspection PyBroadException
                            try:
                                retval.append(Result(await f))
                            except Exception:
                                retval.append(Result(exc_info=sys.exc_info()))
            except Exception:
                for a in awaitables:
                    if not a.done():
                        a.cancel()
                raise

        for group in _priority_groups(functions):
            await multicall_parallel(group)
        return retval

    def _multicall_parallel_sync(self, caller_kwargs, reraise, functions=None):
        """Execute a call into multiple python methods.

        Called from :func:`HookCaller.__call__`.

        """
        # __tracebackhide__ = True
        retval = []
        if functions is None:
            functions = self.functions
        self._call_befores_sync(caller_kwargs=caller_kwargs)
        for hookimpl in reversed(functions):
            kwargs = hookimpl.filtered_args(caller_kwargs)
            if reraise:
                retval.append(hookimpl.function(**kwargs))
            else:
                # noinspection PyBroadException
                try:
                    retval.append(Result(hookimpl.function(**kwargs)))
                except Exception:
                    retval.append(Result(exc_info=sys.exc_info()))
        return retval

    async def _multicall_first(self, caller_kwargs, reraise, functions=None):
        """Execute a call into multiple python methods.

        Called from :func:`HookCaller.__call__`.

        """
        # __tracebackhide__ = True
        await self.plugin_manager.await_unscheduled_coros()
        assert reraise
        if functions is None:
            functions = self.functions
        await self._call_befores(caller_kwargs=caller_kwargs)
        for hookimpl in reversed(functions):
            kwargs = hookimpl.filtered_args(caller_kwargs)
            result = hookimpl.function(**kwargs)
            if hookimpl.is_async:
                result = await result
            if result is not None:
                return result
        return None

    def _multicall_first_sync(self, caller_kwargs, reraise, functions=None):
        """Execute a call into multiple python methods.

        Called from :func:`HookCaller.__call__`.

        """
        # __tracebackhide__ = True
        assert reraise
        if functions is None:
            functions = self.functions
        self._call_befores_sync(caller_kwargs=caller_kwargs)
        for hookimpl in reversed(functions):
            kwargs = hookimpl.filtered_args(caller_kwargs)
            result = hookimpl.function(**kwargs)
            if result is not None:
                return result
        return None


HookCaller.pm = HookCaller.plugin_manager
