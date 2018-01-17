import inspect
import warnings

from .helpers import fqn
from .markers import HookimplMarker, HookspecMarker


class HookCallError(Exception):
    """ Hook was called wrongly.
    """


class HookSpec(object):
    _ALLOWED_PARAMETER_KINDS = {
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD
    }

    def __init__(self, namespace, name, flag_set):
        self.namespace = namespace
        self.name = name
        self.function = getattr(namespace, name)
        self.is_first_result = self.is_replay = self.is_reraise = self.is_sync = False
        self.__dict__.update(HookspecMarker.set2dict(flag_set))
        self.__init_args()

    def __init_args(self):
        signature = inspect.signature(self.function)
        parameters = list(signature.parameters.values())
        if inspect.isclass(self.namespace) and inspect.isfunction(self.function):
            parameters = parameters[1:]
        if any(parameter.kind != inspect.Parameter.POSITIONAL_OR_KEYWORD  # not in self._ALLOWED_PARAMETER_KINDS
               for parameter in parameters):
            raise ValueError(
                "%s.%s%s: Only positional arguments allowed "
                "for hook specifications." %
                (fqn(self.namespace), self.name, signature)
            )
        self.req_args = {
            p.name for p in parameters
            if p.default is inspect.Parameter.empty  # p.kind == inspect.Parameter.POSITIONAL_ONLY
        }
        self.opt_args = {
            p.name: p.default for p in parameters
            if p.default is not inspect.Parameter.empty  # p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        }


class HookValidationError(Exception):
    """ Plugin failed validation.
    """


class HookImpl(object):
    _ALLOWED_PARAMETER_KINDS = {
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD
    }

    def __init__(self, plugin, name, flag_set):
        self.plugin = plugin
        self.name = name
        self.function = getattr(plugin, name)
        self.is_try_first = self.is_try_last = self.is_dont_await = self.is_before = False
        self.__dict__.update(HookimplMarker.set2dict(flag_set))
        # noinspection PyUnresolvedReferences
        self.is_async = (inspect.iscoroutinefunction(self.function) and
                         not self.is_dont_await)
        self.__init_args()

    def __init_args(self):
        signature = inspect.signature(self.function)
        parameters = list(signature.parameters.values())
        if any(parameter.kind != inspect.Parameter.POSITIONAL_OR_KEYWORD  # not in self._ALLOWED_PARAMETER_KINDS
               for parameter in parameters):
            raise ValueError(
                "%s.%s%s: Only positional arguments allowed "
                "for hook specifications." %
                (fqn(self.plugin), self.name, signature)
            )
        self.req_args = {
            p.name for p in parameters
            if p.default is inspect.Parameter.empty  # p.kind == inspect.Parameter.POSITIONAL_ONLY
        }
        self.opt_args = {
            p.name: p.default for p in parameters
            if p.default is not inspect.Parameter.empty  # p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        }

    def filtered_args(self, kwargs):
        return {
            name: value for (name, value) in kwargs.items()
            if name in self.req_args or name in self.opt_args
        }

    def validate_against(self, spec: HookSpec):
        # positional arg checking
        notinspec = self.req_args - spec.req_args - \
                    set(spec.opt_args.keys())
        if notinspec:
            raise HookValidationError(
                "%s.%s: required argument(s) %s in the hook function "
                "are not in the hook specification." %
                (fqn(self.plugin), self.name, notinspec)
            )
        for arg_name, default_value in self.opt_args.items():
            if arg_name in spec.opt_args and \
                    default_value != spec.opt_args[arg_name]:
                warnings.warn(
                    "Hook function %s.%s: optional argument '%s' has other "
                    "default value than the corresponding hook specification." %
                    (fqn(self.plugin), self.name, arg_name)
                )
        # noinspection PyUnresolvedReferences
        if self.is_async and spec.is_sync:
            raise HookValidationError(
                "%s.%s: asynchronous hook function not allowod by hook spec." %
                (fqn(self.plugin), self.name)
            )

        # noinspection PyUnresolvedReferences
        if (self.is_try_first or self.is_try_last) and not spec.is_first_result:
            warnings.warn(
                "Hook function %s.%s: `try_first` and `try_last` qualifiers "
                "only have meaning for hooks specified as `first_result`." %
                (fqn(self.plugin), self.name)
            )
