import weakref

from .hooks import HookSpec
from .multicall import *


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
        multicall_ = multicall_parallel_sync if self.spec.is_sync else multicall_parallel
        reraise = False
        if self.spec:
            notinspec = set(kwargs.keys()) - self.spec.req_args - \
                        set(self.spec.opt_args.keys())
            if notinspec:
                raise TypeError(
                    # TODO: show spec signature
                    "Argument(s) {} not declared in hookspec".format(notinspec),
                )
            notincall = self.spec.req_args - set(kwargs.keys())
            if notincall:
                raise TypeError(
                    # TODO: show spec signature
                    "Missing required argument(s): {}".format(notincall)
                )
            reraise = self.spec.is_reraise
            if self.spec.is_first_result:
                multicall_ = multicall_first_sync if self.spec.is_sync else multicall_first
            if self.spec.is_replay:
                self.plugin_manager.history.append((self.name, kwargs))
        return multicall_(
            before=self.before,
            functions=self.functions,
            caller_kwargs=kwargs,
            reraise=reraise
        )

    def replay_to(self, hookimpl, kwargs):
        multicall_parallel_sync(
            before=self.before,
            functions=[hookimpl.function],
            caller_kwargs=kwargs,
            reraise=False
        )


HookCaller.pm = HookCaller.plugin_manager
