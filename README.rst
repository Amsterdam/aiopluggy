aiopluggy - A minimalist production ready plugin system
=======================================================

Please `read the docs`_ to learn more!


Changes since `pluggy`_
-----------------------

*   Removed all deprecated code, including the legacy ``__multicall__`` parameter
    handling.
*   Renamed from **pluggy** to **aiopluggy**
*   Made asynchronous.
*   Removed compatibility with Python versions \<3.5.
*   Updated documentation.
*   Removed unused badges.


A definitive example
--------------------

.. code-block:: python

    import aiopluggy

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
        @hookimpl
        def myhook(self, arg1, arg2):
            print("inside Plugin_1.myhook()")
            return arg1 + arg2


    class Plugin_2(object):
        """A 2nd hook implementation namespace.
        """
        @hookimpl
        def myhook(self, arg1, arg2):
            print("inside Plugin_2.myhook()")
            return arg1 - arg2


    # create a manager and add the spec
    pm = aiopluggy.PluginManager("myproject")
    pm.add_hookspecs(MySpec)

    # register plugins
    pm.register(Plugin_1())
    pm.register(Plugin_2())

    # call our `myhook` hook
    results = pm.hook.myhook(arg1=1, arg2=2)
    print(results)


.. links
.. _read the docs:
    https://aiopluggy.readthedocs.io/en/latest/
