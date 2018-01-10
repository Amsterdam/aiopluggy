import inspect
import warnings

from .helpers import (
    format_def, get_canonical_name, varnames, PluginValidationError
)
from .hook_impl import HookImpl, HookCallError
from .markers import HookspecMarker, HookimplMarker
from .multicall import (
    multicall_first, multicall_parallel, Result
)


VERSION = '0.1.3rc2'

__all__ = [
    'HookimplMarker', 'HookspecMarker',
    'PluginManager', 'PluginValidationError',
    'HookCallError', 'VERSION'
]


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

    def __init__(self, project_name, implprefix=None):
        """ if implprefix is given implementation functions
        will be recognized if their name matches the implprefix. """
        self.project_name = project_name
        self.implmarker = '_pluggy_%s_impl' % project_name
        self.specmarker = '_pluggy_%s_spec' % project_name
        self.implprefix = implprefix
        self.hooks = _Namespace()
        self.name2plugin = {}

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
                hc = HookCaller(name)
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

    async def register(self, namespace):
        """ Register a plugin and return its canonical name.

        Raises:
             ValueError: if the plugin is already registered.

        """
        plugin_name = get_canonical_name(namespace)
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
                namespace, plugin_name, name, hookimpl_flagset
            )
            hc = getattr(self.hooks, name, None)
            if hc is None:
                hc = HookCaller(name)
                setattr(self.hooks, name, hc)
            elif hc.spec:
                hookimpl.verify_hookspec(hc.spec)
                await hc.maybe_apply_history(hookimpl)
            # noinspection PyTypeChecker
            hc.add_hookimpl(hookimpl)
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
        if flag_set is None and self.implprefix and name.startswith(self.implprefix):
            flag_set = set()
        return flag_set

    def check_pending(self):
        """

        Verify that all hooks which have not been verified against a hooks
        specification are optional, otherwise raise PluginValidationError

        """
        for name in self.hooks.__dict__:
            if name[0] == "_":
                continue
            hook = getattr(self.hooks, name)
            if hook.spec:
                continue
            for hookimpl in (hook.wrappers + hook.nonwrappers):
                if not hookimpl.is_optional:
                    raise PluginValidationError(
                        "unknown hooks %r in plugin %r" %
                        (name, hookimpl.plugin))


class _Namespace(object):
    pass


class Spec(object):

    def __init__(self, namespace, name, flag_set):
        self.namespace = namespace
        self.name = name
        self.argnames, self.kwargnames = varnames(namespace, name)
        self.__dict__.update(HookspecMarker.set2dict(flag_set))


class HookCaller(object):
    def __init__(self, name):
        self.name = name
        self.wrappers = []
        self.implementations = []
        self.spec = None
        self.call_history = []

    def set_spec(self, namespace, flag_set):
        assert self.spec is None
        self.spec = Spec(namespace, self.name, flag_set)
        for hookimpl in (self.wrappers + self.implementations):
            hookimpl.verify_hookspec(self.spec)

    def add_hookimpl(self, hookimpl):
        """A an implementation to the callback chain.
        """
        if hookimpl.is_wrapper:
            methods = self.wrappers
        else:
            methods = self.implementations

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
        if self.spec and self.spec.is_historic:
            raise RuntimeError(
                "Hook %s is specified as historic. "
                "Use call_historic() instead" % self.name
            )
        if self.spec:
            notincall = set(self.spec.argnames) - set(
                kwargs.keys()
            )
            if notincall:
                warnings.warn(
                    "Argument(s) {} which are declared in the hookspec "
                    "can not be found in this hook call"
                    .format(tuple(notincall)),
                    stacklevel=2,
                )
        if self.spec and self.spec.is_first_result:
            return multicall_first(
                self.wrappers,
                self.implementations,
                kwargs
            )
        return multicall_parallel(
            self.wrappers,
            self.implementations,
            kwargs
        )

    async def call_historic(self, kwargs=None, proc=None, exc_hdlr=None):
        """ call the hook with given ``kwargs`` for all registered plugins and
        for all plugins which will be registered afterwards.

        If ``proc`` is not None it will be called for for each non-None result
        obtained from a hook implementation.
        """
        if kwargs is None:
            kwargs = {}
        if self.spec is None or not self.spec.is_historic:
            raise RuntimeError(
                "Hook %s is not specified as historic"
            )
        self.call_history.append((kwargs, proc, exc_hdlr))
        res = await multicall_parallel(
            self.wrappers, self.implementations, kwargs,
            return_exceptions=True
        )
        for x in res:
            try:
                value = x.value
                if proc:
                    proc(value)
            except Exception as e:
                if exc_hdlr:
                    exc_hdlr(e)

    async def maybe_apply_history(self, hookimpl):
        """Apply call history to a new hookimpl if it is marked as historic.
        """
        if self.spec.is_historic:
            for kwargs, proc, exc_hdlr in self.call_history:
                try:
                    res = await multicall_first(
                        self.wrappers, [hookimpl], kwargs
                    )
                except Exception as e:
                    if exc_hdlr:
                        exc_hdlr(e)
                else:
                    if proc:
                        proc(res)
