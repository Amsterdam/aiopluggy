class HookspecMarker(object):
    """ Decorator helper class for marking functions as hook specifications.

    You can instantiate it with a project_name to get a decorator.
    Calling PluginManager.register_specs later will discover all marked functions
    if the PluginManager uses the same project_name.
    """
    QUALIFIERS = {'first_result', 'replay', 'reraise', 'sync', 'required'}

    def __init__(self, project_name, flags=None):
        if flags is None:
            flags = set()
        if 'first_result' in flags:
            flags.add('reraise')
        self.project_name = project_name
        self.specmarker = '_pluggy_%s_spec' % project_name
        self.flags = flags

    def __call__(self, func):
        setattr(func, self.specmarker, self.flags)
        return func

    @property
    def first_result(self):
        return self._with_flag('first_result')

    @property
    def replay(self):
        return self._with_flag('replay')

    @property
    def required(self):
        return self._with_flag('required')

    @property
    def reraise(self):
        return self._with_flag('reraise')

    @property
    def sync(self):
        return self._with_flag('sync')

    def _with_flag(self, name):
        if name not in self.QUALIFIERS:
            raise AttributeError(name)
        flags = self.flags.union({name})
        return HookspecMarker(self.project_name, flags)

    @classmethod
    def set2dict(cls, s):
        return {
            ('is_' + name): (name in s) for name in cls.QUALIFIERS
        }


class HookimplMarker(object):
    # language=rst
    """ Decorator helper class for marking functions as hook implementations.

    You can instantiate with a project_name to get a decorator.
    Calling PluginManager.register later will discover all marked functions
    if the PluginManager uses the same project_name.
    """

    QUALIFIERS = {'try_first', 'try_last', 'dont_await', 'before'}

    def __init__(self, project_name, flags=None):
        if flags is None:
            flags = set()
        if {'try_first', 'try_last'} <= flags:
            raise AttributeError(
                "Hook can not be both 'try_first' and 'try_last'."
            )
        self.project_name = project_name
        self.implmarker = '_pluggy_%s_impl' % project_name
        self.flags = flags

    def __call__(self, func):
        setattr(func, self.implmarker, self.flags)
        return func

    @property
    def before(self):
        return self._with_flag('before')

    @property
    def dont_await(self):
        return self._with_flag('dont_await')

    @property
    def try_first(self):
        return self._with_flag('try_first')

    @property
    def try_last(self):
        return self._with_flag('try_last')

    def _with_flag(self, name):
        if name not in self.QUALIFIERS:
            raise AttributeError()
        flags = self.flags.union({name})
        return HookimplMarker(self.project_name, flags)

    @classmethod
    def set2dict(cls, s):
        return {
            ('is_' + name): (name in s) for name in cls.QUALIFIERS
        }
