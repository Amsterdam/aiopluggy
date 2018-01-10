import pytest

from aiopluggy import *


hookspec = HookspecMarker("example")
hookimpl = HookimplMarker("example")


@pytest.mark.asyncio
async def test_plugin_double_register(pm: PluginManager):
    class EmptyPlugin(object):
        pass
    await pm.register(EmptyPlugin)
    with pytest.raises(ValueError):
        await pm.register(EmptyPlugin)
    with pytest.raises(ValueError):
        await pm.register(EmptyPlugin)


def test_add_hookspecs_from_class(pm: PluginManager):
    class HookSpec(object):
        @classmethod
        @hookspec
        def some_method(cls, arg1, arg2):
            pass
    pm.add_hookspecs(HookSpec)
    assert pm.hooks.some_method.spec.argnames == ('arg1', 'arg2')


def test_add_hookspecs_from_object(pm: PluginManager):
    class HookSpec(object):
        @hookspec
        def some_method(self, arg1, arg2):
            pass
    pm.add_hookspecs(HookSpec())
    assert pm.hooks.some_method.spec.argnames == ('arg1', 'arg2')


def test_add_hookspecs_from_module(pm: PluginManager):
    import plugin_namespace as module
    pm.add_hookspecs(module)
    assert pm.hooks.function_spec.spec.argnames == ('arg1', 'arg2')
    assert pm.hooks.callable_spec.spec.argnames == ('arg1', 'arg2')
    assert pm.hooks.class1_spec.spec.argnames == ('arg1', 'arg2')
    assert pm.hooks.class2_spec.spec.argnames == ('arg1', 'arg2')


@pytest.mark.asyncio
async def test_add_hookimpls_from_class(pm: PluginManager):
    class HookSpec(object):
        @classmethod
        @hookimpl
        def some_method(cls, arg1, arg2):
            pass

        @classmethod
        def example_plugin_impl(cls, arg1, arg2):
            pass
    await pm.register(HookSpec)
    assert len(pm.hooks.some_method.implementations) == 1
    assert len(pm.hooks.example_plugin_impl.implementations) == 1


@pytest.mark.asyncio
async def test_add_hookimpls_from_object(pm: PluginManager):
    class HookSpec(object):
        @hookimpl
        def some_method(self, arg1, arg2):
            pass

        def example_plugin_impl(self, arg1, arg2):
            pass
    await pm.register(HookSpec())
    assert len(pm.hooks.some_method.implementations) == 1
    assert len(pm.hooks.example_plugin_impl.implementations) == 1


@pytest.mark.asyncio
async def test_add_hookimpls_from_module(pm: PluginManager):
    import plugin_namespace as module
    await pm.register(module)
    assert len(pm.hooks.function_impl.implementations) == 1
    assert len(pm.hooks.callable_impl.implementations) == 1
    assert len(pm.hooks.class1_impl.implementations) == 1
    assert len(pm.hooks.class2_impl.implementations) == 1
    assert len(pm.hooks.example_plugin_impl.implementations) == 1
