import pytest

from aiopluggy import *


hookspec = HookspecMarker("example")
hookimpl = HookimplMarker("example")


def test_plugin_double_register(pm: PluginManager):
    class EmptyPlugin(object):
        pass
    pm.register(EmptyPlugin)
    with pytest.raises(ValueError):
        pm.register(EmptyPlugin)
    with pytest.raises(ValueError):
        pm.register(EmptyPlugin)


def test_register_specs_from_class(pm: PluginManager):
    class HookSpec(object):
        @classmethod
        @hookspec
        def some_class_method(cls, arg1, arg2, foo='bar'):
            pass
        @hookspec
        def some_instance_method(self, arg1, arg2, foo='bar'):
            pass
    pm.register_specs(HookSpec)
    assert pm.hooks.some_class_method.spec.req_args == {'arg1', 'arg2'}
    assert pm.hooks.some_class_method.spec.opt_args == {'foo': 'bar'}
    assert pm.hooks.some_instance_method.spec.req_args == {'arg1', 'arg2'}
    assert pm.hooks.some_instance_method.spec.opt_args == {'foo': 'bar'}


def test_register_specs_from_object(pm: PluginManager):
    class HookSpec(object):
        @hookspec
        def some_method(self, arg1, arg2, foo='bar'):
            pass
    pm.register_specs(HookSpec())
    assert pm.hooks.some_method.spec.req_args == {'arg1', 'arg2'}
    assert pm.hooks.some_method.spec.opt_args == {'foo': 'bar'}


def test_register_specs_from_module(pm: PluginManager):
    import plugin_spec
    pm.register_specs(plugin_spec)
    assert pm.hooks.function_spec.spec.req_args == {'arg1', 'arg2'}
    assert pm.hooks.function_spec.spec.opt_args == {'foo': 'bar'}


@pytest.mark.asyncio
async def test_add_hookimpls_from_class(pm: PluginManager):
    class HookSpec(object):
        @classmethod
        @hookimpl
        def some_method(cls, arg1, arg2):
            pass

    pm.register(HookSpec)
    assert len(pm.hooks.some_method.functions) == 1


@pytest.mark.asyncio
async def test_add_hookimpls_from_object(pm: PluginManager):
    class HookSpec(object):
        @hookimpl
        def some_method(self, arg1, arg2):
            pass
    pm.register(HookSpec())
    assert len(pm.hooks.some_method.functions) == 1


@pytest.mark.asyncio
async def test_add_hookimpls_from_module(pm: PluginManager):
    import plugin as module
    pm.register(module)
    assert len(pm.hooks.function_impl.functions) == 1
    assert len(pm.hooks.class1_impl.functions) == 1
    assert len(pm.hooks.class2_impl.functions) == 1


@pytest.mark.asyncio
async def test_replay(pm: PluginManager):
    out = []

    class Spec:
        @hookspec.replay
        def replay_me1(self, arg):
            pass

        @hookspec.replay
        def replay_me2(self, arg):
            pass

    class Impl:
        @hookimpl
        def replay_me1(self, arg):
            out.append(arg)

        @hookimpl
        async def replay_me2(self, arg):
            out.append(arg)

    pm.register_specs(Spec)
    await pm.hooks.replay_me1(arg=1)
    await pm.hooks.replay_me2(arg=2)
    pm.register(Impl())
    assert out == [1]
    await pm.hooks.replay_me1(arg=3)
    assert out == [1, 2, 3]
