import warnings

from .helpers import format_def, PluginValidationError, varnames
from .markers import HookimplMarker


class HookCallError(Exception):
    """ Hook was called wrongly.
    """


class HookImpl(object):
    def __init__(self, plugin, plugin_name, func, flag_set):
        self.function = func
        self.argnames, self.kwargnames = varnames(self.function)
        self.plugin = plugin
        self.plugin_name = plugin_name
        self.__dict__.update(HookimplMarker.set2dict(flag_set))

    def filtered_args(self, kwargs):
        try:
            return [kwargs[argname] for argname in self.argnames]
        except KeyError:
            missing = {
                argname for argname in self.argnames
                if argname not in kwargs
            }
            raise HookCallError(
                "hook call must provide argument(s) %r" % missing
            ) from None

    def verify_hookspec(self, hookspec):
        # positional arg checking
        notinspec = set(self.argnames) - set(hookspec.argnames)
        if notinspec:
            raise PluginValidationError(
                "Plugin %r for hooks %r\nhookimpl definition: %s\n"
                "Argument(s) %s are declared in the hookimpl but "
                "can not be found in the hookspec" %
                (self.plugin_name, hookspec.name,
                 format_def(self.function), notinspec)
            )
        # noinspection PyUnresolvedReferences
        if not hookspec.is_first_result and self.is_asyncio and (
            self.is_try_first or self.is_try_last
        ):
            warnings.warn(
                "Asynchronous hook implementation %s uses call prioritization, "
                "but this only works for 'first_result'-style hooks. For this "
                "hook, the call order of asynchronous hook implementations is "
                "undefined." % format_def(self.function)
            )
