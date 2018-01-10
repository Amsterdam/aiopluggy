_HOOK_SPEC_ATTRS = {'first_result', 'historic'}


class HookspecMarker(object):
    """ Decorator helper class for marking functions as hook specifications.

    You can instantiate it with a project_name to get a decorator.
    Calling PluginManager.add_hookspecs later will discover all marked functions
    if the PluginManager uses the same project_name.
    """

    def __init__(self, project_name, flags=None):
        if flags is None:
            flags = set()
        self.project_name = project_name
        self.specmarker = '_pluggy_%s_spec' % project_name
        self.flags = flags

    def __call__(self, func):
        """ if passed a function, directly sets attributes on the function
        which will make it discoverable to add_hookspecs().  If passed no
        function, returns a decorator which can be applied to a function
        later using the attributes supplied.

        If firstresult is True the 1:N hook call (N being the number of registered
        hook implementation functions) will stop at I<=N when the I'th function
        returns a non-None result.

        If historic is True calls to a hook will be memorized and replayed
        on later registered plugins.

        """
        setattr(func, self.specmarker, self.flags)
        return func

    def __getattr__(self, name):
        if name not in _HOOK_SPEC_ATTRS:
            raise AttributeError()
        flags = self.flags.union({name})
        if {'first_result', 'historic'} <= flags:
            raise AttributeError(
                "Hook spec can not be both 'historic' and 'first_result'."
            )
        return HookspecMarker(self.project_name, flags)

    @staticmethod
    def set2dict(s):
        return {
            ('is_' + name): (name in s) for name in _HOOK_SPEC_ATTRS
        }


_HOOK_IMPL_ATTRS = {'wrapper', 'asyncio', 'optional', 'try_first', 'try_last'}


class HookimplMarker(object):
    """ Decorator helper class for marking functions as hook implementations.

    You can instantiate with a project_name to get a decorator.
    Calling PluginManager.register later will discover all marked functions
    if the PluginManager uses the same project_name.
    """

    def __init__(self, project_name, flags=None):
        if flags is None:
            flags = set()
        self.project_name = project_name
        self.implmarker = '_pluggy_%s_impl' % project_name
        self.flags = flags

    def __call__(self, func):

        """ if passed a function, directly sets attributes on the function
        which will make it discoverable to register().  If passed no function,
        returns a decorator which can be applied to a function later using
        the attributes supplied.

        If optionalhook is True a missing matching hook specification will not result
        in an error (by default it is an error if no matching spec is found).

        If try_first is True this hook implementation will run as early as possible
        in the chain of N hook implementations for a specfication.

        If try_last is True this hook implementation will run as late as possible
        in the chain of N hook implementations.

        If hookwrapper is True the hook implementations needs to execute exactly
        one "yield".  The code before the yield is run early before any non-hookwrapper
        function is run.  The code after the yield is run after all non-hookwrapper
        function have run.  The yield receives a ``Result`` object representing
        the exception or result outcome of the inner calls (including other hookwrapper
        calls).

        """
        setattr(func, self.implmarker, self.flags)
        return func

    def __getattr__(self, name):
        if name not in _HOOK_IMPL_ATTRS:
            raise AttributeError()
        flags = self.flags.union({name})
        if {'try_first', 'try_last'} <= flags:
            raise AttributeError(
                "Hook can not be both 'try_first' and 'try_last'."
            )
        return HookimplMarker(self.project_name, flags)

    @staticmethod
    def set2dict(s):
        return {
            ('is_' + name): (name in s) for name in _HOOK_IMPL_ATTRS
        }
