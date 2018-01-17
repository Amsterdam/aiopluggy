import inspect
import warnings

from .helpers import fqn
from .hooks import HookImpl
from .hookcaller import HookCaller


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
        self.name2plugin = {}
        self.history = []  # list of (name, kwargs) tuples in historic order.
        self.replay_to = {}  # HookImpl objects, indexed by name

    def add_hookspecs(self, namespace):
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
        if plugin_name in self.name2plugin:
            raise ValueError("Plugin already registered: %s=%s" %
                             (plugin_name, namespace))

        # XXX if an error happens we should make sure no state has been
        # changed at point of return
        self.name2plugin[plugin_name] = namespace

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

        self.replay_history()
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

    def replay_history(self):
        if not self.replay_to:
            return
        for name, kwargs in self.history:
            if name in self.replay_to:
                hookimpl = self.replay_to[name]
                hook = getattr(self.hooks, name)
                hook.replay_to(hookimpl, kwargs)
        self.replay_to = {}
