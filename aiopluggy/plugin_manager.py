import inspect
import warnings

from .helpers import fqn
from .hooks import HookImpl
from .hook_caller import HookCaller


class PluginManager(object):
    """ Core Pluginmanager class which manages registration
    of plugin objects and 1:N hook calling.

    You can register new hooks by calling ``add_hookspec(module_or_class)``.
    You can register plugin objects (which contain hooks) by calling
    ``register(plugin)``.  The Pluginmanager is initialized with a
    prefix that is searched for in the names of the dict of registered
    plugin objects.

    For debugging purposes you can call ``enable_tracing()``
    which will subsequently send debug information to the trace helper.
    """

    class _Namespace(object):
        pass

    def __init__(self, project_name):
        self.project_name = project_name
        self.implmarker = '_pluggy_%s_impl' % project_name
        self.specmarker = '_pluggy_%s_spec' % project_name
        self.hooks = self._Namespace()
        self.registered_plugins = set()
        self.history = []  # list of (name, kwargs) tuples in historic order.
        self.replay_to = {}  # HookImpl objects, indexed by name
        self.unscheduled_coros = []
        """:type: list(tuple(aiopluggy.hooks.HookImpl, Coroutine))"""
        self.unhandled_exceptions = []
        """:type: list(tuple(aiopluggy.hooks.HookImpl, Exception))"""

    def register_specs(self, namespace):
        """ add new hook specifications defined in the given module_or_class.
        Functions are recognized if they have been decorated accordingly. """
        names = []
        for name in dir(namespace):
            spec_flag_set = self._get_hookspec_flag_set(namespace, name)
            if spec_flag_set is None:
                continue
            hc = getattr(self.hooks, name, None)
            if hc is None:
                hc = HookCaller(name, self)
                setattr(self.hooks, name, hc)
            # plugins registered this hook without knowing the spec
            hc.set_spec(namespace, spec_flag_set)
            names.append(name)

        if len(names) == 0:
            warnings.warn(
                "did not find any %r hooks in %r" %
                (self.project_name, namespace)
            )
        return names

    def register(self, namespace):
        """ Register a plugin and return its canonical name.

        Raises:
             ValueError: if the plugin is already registered.

        """
        plugin_name = fqn(namespace)
        if plugin_name in self.registered_plugins:
            raise ValueError("Plugin already registered: %s=%s" %
                             (plugin_name, namespace))

        # XXX if an error happens we should make sure no state has been
        # changed at point of return
        self.registered_plugins.add(plugin_name)

        for name in dir(namespace):
            hookimpl_flagset = self._get_hookimpl_flag_set(namespace, name)
            if hookimpl_flagset is None:
                continue
            hookimpl = HookImpl(
                namespace, name, hookimpl_flagset
            )
            hook_caller = getattr(self.hooks, name, None)
            if hook_caller is None:
                hook_caller = HookCaller(name, self)
                setattr(self.hooks, name, hook_caller)
            # noinspection PyTypeChecker
            hook_caller.add_hookimpl(hookimpl)
            if hook_caller.spec and hook_caller.spec.is_replay:
                self.replay_to[hookimpl.name] = hookimpl

        self._replay_history()
        return plugin_name

    def _get_hookspec_flag_set(self, namespace, name):
        thing = getattr(namespace, name)
        if not inspect.isroutine(thing):
            return None
        flag_set = getattr(thing, self.specmarker, None)
        return flag_set

    def _get_hookimpl_flag_set(self, plugin, name):
        thing = getattr(plugin, name)
        if not inspect.isroutine(thing) and not inspect.isclass(thing):
            return None
        flag_set = getattr(thing, self.implmarker, None)
        if flag_set is None and inspect.isclass(thing):
            flag_set = getattr(thing.__init__, self.implmarker, None)
        return flag_set

    def redundant(self):
        """Dictionary of ``first_only`` hooks with multiple implementations."""
        result = {}
        for name, hookcaller in self.hooks.__dict__.items():
            if name[0] == "_":
                continue
            spec = hookcaller.spec
            if spec is not None and spec.is_first_only and len(hookcaller.functions) > 1:
                result[name] = hookcaller
        return result

    def unspecified(self):
        """Dictionary of implemented hooks without specification."""
        result = {}
        for name in self.hooks.__dict__:
            if name[0] == "_":
                continue
            hook = getattr(self.hooks, name)
            if hook.spec is None:
                result[name] = hook
        return result

    def unimplemented(self):
        """Dictionary of specified hooks without implementation."""
        result = {}
        for name in self.hooks.__dict__:
            if name[0] == "_":
                continue
            hook = getattr(self.hooks, name)
            if hook.spec is not None and len(hook.functions) == 0:
                result[name] = hook
        return result

    def missing(self):
        """Dictionary of specified required hooks without implementation."""
        result = {}
        for name in self.hooks.__dict__:
            if name[0] == "_":
                continue
            hook = getattr(self.hooks, name)
            if hook.spec is not None and hook.spec.is_required and len(hook.functions) == 0:
                result[name] = hook
        return result

    def _replay_history(self):
        if len(self.replay_to) == 0:
            return
        for name, kwargs in self.history:
            if name not in self.replay_to:
                continue
            hookimpl = self.replay_to[name]
            hookcaller = getattr(self.hooks, name)
            """:type: aiopluggy.hook_caller.HookCaller"""
            if hookimpl.is_async or any(
                b.is_async for b in hookcaller.before
            ):
                self.unscheduled_coros.append((
                    hookimpl,
                    hookcaller._multicall_first_async(
                        kwargs, first_only=True, functions=[hookimpl]
                    )
                ))
            else:
                try:
                    hookcaller.replay(hookimpl, kwargs)
                except Exception as e:
                    self.unhandled_exceptions.append((hookimpl, e))
        self.replay_to = {}

    async def await_unscheduled_coros(self):
        for hookimpl, coro in self.unscheduled_coros:
            try:
                await coro
            except Exception as e:
                self.unhandled_exceptions.append((hookimpl, e))
