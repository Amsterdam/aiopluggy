import aiopluggy, asyncio

hookspec = aiopluggy.HookspecMarker("myproject")
hookimpl = aiopluggy.HookimplMarker("myproject")


class MySpec(object):
    """A hook specification namespace.
    """
    @hookspec
    def myhook(self, arg1, arg2):
        """My special little hook that you can customize.
        """


class Plugin_1(object):
    """A hook implementation namespace.
    """
    @hookimpl.asyncio
    async def myhook(self, arg1, arg2):
        print("inside Plugin_1.myhook()")
        return arg1 + arg2


class Plugin_2(object):
    """A 2nd hook implementation namespace.
    """
    @hookimpl
    def myhook(self, arg1, arg2):
        print("inside Plugin_2.myhook()")
        return arg1 - arg2


async def main():
    # create a manager and add the spec
    pm = aiopluggy.PluginManager("myproject")
    pm.add_hookspecs(MySpec)

    # register plugins
    await pm.register(Plugin_1())
    await pm.register(Plugin_2())

    # call our `myhook` hook
    results = await pm.hooks.myhook(arg1=1, arg2=2)
    values = [ result.value for result in results ]
    print(values)


asyncio.get_event_loop().run_until_complete(main())
