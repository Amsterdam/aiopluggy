.. _tutorial:

Tutorial
========
.. highlight:: python

How does it work?
-----------------
A *plugin* is a :ref:`namespace <tut-scopes>` which defines hook functions.

``aiopluggy`` manages *plugins* by relying on:

- hook *specifications* - which specify function signatures
- hook *implementations* - which implement such functions
- the *hook caller* - a call loop which collects results

where for each registered hook *specification*, a *hook call* will invoke up to
``N`` registered hook *implementations*.

``aiopluggy`` accomplishes all this by implementing a `request-response pattern`_ using *function*
subscriptions and can be thought of and used as a rudimentary busless `publish-subscribe`_
event system.

``aiopluggy``'s approach is meant to let a designer think carefuly about which objects are
explicitly needed by an extension writer. This is in contrast to subclass-based extension
systems which may expose unecessary state and behaviour or encourage `tight coupling`_
in overlying frameworks.


A first example
---------------

.. literalinclude:: examples/firstexample.py

Running this directly gets us:

.. code-block:: text

    $ python docs/examples/firstexample.py

    inside Plugin_2.myhook()
    inside Plugin_1.myhook()
    [-1, 3]

For more details and advanced usage please read on.


.. _what_is_a_plugin:

What is a Plugin?
-----------------
A **plugin** is a namespace object (currently either a :ref:`module <tut-modules>`,
a :ref:`class <tut-classes>`, or an :ref:`instance object <tut-instanceobjects>`)
which implements a set of *hook functions*.

**plugins** are managed by an instance of a :class:`~aiopluggy.PluginManager`,
which defines the primary ``aiopluggy`` API. In order for a ``PluginManager`` to
detect *hook functions* in a namespace, they must be decorated using special
``aiopluggy`` *hook markers*.

When a hook is implemented by more than one plugin, the *default behaviour* of
the :class:`~aiopluggy.PluginManager` is to call *all* implementations, and
return a list of results. Alternatively, you can instruct the plugin manager to
call the implementations one-by-one, until one of them returns a non-``None``
value, and return this single value (see :ref:`first_result`).


.. _marking_implementations:

Marking hook implementations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:class:`~aiopluggy.HookimplMarker` decorators are used to *mark* functions as
*hook implementations*. For example::

    from aiopluggy import HookimplMarker

    hookimpl = HookimplMarker('My Project')

    @hookimpl
    def send_greetings_to(name):
        print("Hi there, %s!" % name)

.. note::

    :class:`~aiopluggy.HookimplMarker` is a *class*. Only
    :class:`~aiopluggy.HookimplMarker` *instances* can be used as decorator.

:class:`~aiopluggy.HookimplMarker` requires a ``project_name`` string as a
constructor argument. Implementations marked with the created instance will only
be detected by a :class:`~aiopluggy.PluginManager` that is explicitly
set to detect hooks with this ``project_name``. This allows
you to have distinct sets of hooks in your program, each managed by its own
plugin manager instance.


Asynchronous hook implementations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Hook implementations can be asynchronous::

    @hookimpl
    async def read_data_from(file_descriptor):
        ...  # some asynchronous operations

.. note::

    *Asynchronous* functions and methods are :func:`automatically detected
    <inspect.iscoroutinefunction>` by the :class:`~aiopluggy.PluginManager`,
    and :ref:`awaited <await>` at call-time. This feature is the whole
    *raison-d’être* for the ``aiopluggy`` package, really.


Hook wrappers
^^^^^^^^^^^^^
Normal hooks functions can not be generators, ie. they may only
:ref:`return <return>` results, and never :ref:`yield <yield>` anything.

A hook function that *does* yield is treated by the
:class:`~aiopluggy.PluginManager` as a **hook wrapper**. This means that the
function will be called to *wrap* (or surround) all other normal hook function
calls. A **hook wrapper** can thus execute some code ahead of, and after, the
execution of all corresponding non-wrapppers.

Much in the same way as a :func:`context manager <contextlib.contextmanager>`, a
*hook wrapper* must be implemented as generator function with a single
:ref:`yield <yield>` in its body::

    @hookimpl
    def some_hook(arg1, arg2):
        """
        Wrap calls to ``some_hook()`` implementations, which may raise an exception.
        """
        if config.debug:
            print("Pre-hook argument values: %r, %r" % (arg1, arg2))

        # all corresponding hookimpls are invoked here:
        results = yield

        for result in results:
            try:
                result.value
            except:
                result.value = None

        if config.debug:
            print("Post-hook argument values: %r, %r" % (arg1, arg2))

The generator is `sent`_ a list of :class:`~aiopluggy.Result` objects which is
assigned in the ``yield`` expression and used to update the ``config``
dictionary.

Hook wrappers can not *return* results (as per generator function semantics);
they can only modify them by changing the :attr:``Result.value`` attribute.


Hook implementation qualifiers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Furthermore, :class:`~aiopluggy.HookimplMarker` can be used to configure the
call-time behavior of a hook. For example, there's the :ref:`try_first`
qualifier::

    @hookimpl.try_first
    def get_one_message():
        return "Hello world!"

The :ref:`try_first` qualifier instructs the plugin manager to try this
implementation before all other implementations not marked as :ref:`try_first`.

Currently, ``aiopluggy`` supports the following qualifiers for hook implementations:

-   :ref:`try_first` and :ref:`try_last`
-   ``dont_await``

Some of these qualifiers may be combined, too::

    @hookimpl.try_first.dont_await
    async def get_one_message():
        return await aioredis.get('my-message')

Each qualifier is explained in more detail below.


.. _try_first:
.. _try_last:

``try_first`` and ``try_last``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
By default, hooks are :ref:`called <calling>` in LIFO registered order. However,
a *hook function* can influence its call-time invocation position. If marked
with a ``tryfirst`` or ``trylast`` qualifier, it will be executed *first* or
*last* respectively in the hook call loop:

.. code-block:: python

    from aiopluggy import PluginManager, HookimplMarker
    import asyncio

    hookimpl = HookimplMarker('my_project')
    result = []

    class Plugin1:
        @hookimpl
        def my_hook(self):
            result.append(1)

    class Plugin2:
        @hookimpl.try_last  # Execute after other hooks.
        def my_hook(self):
            result.append(2)

    pm = PluginManager('my_project')
    pm.register(Plugin1())
    pm.register(Plugin2())
    asyncio.get_event_loop().run_until_complete(pm.hooks.my_hook())
    print(result)

Will output ``[1, 2]``, even though ``Plugin2`` was registered *after*
``Plugin1`` and would normally be called first.

.. todo::

    Write something about asynchronous hook functions in relation to call ordering and the :ref:`first_result` qualifier.


``dont_await``
^^^^^^^^^^^^^^
:term:`coroutine functions <coroutine function>` are :func:`automatically
detected <inspect.iscoroutinefunction>` by the
:class:`~aiopluggy.PluginManager`, and :ref:`awaited <await>` at call-time. But
what if the caller should receive the :class:`~asyncio.Future` object returned
by the coroutine function, instead of having this future object awaited by the
plugin manager?

As a workaround, you could wrap the coroutine function in a synchronous
function, like this::

    @hookimpl
    def get_some_awaitable():
        async def read_from_database():
            ...  # Do something
        return read_from_database()

This will work, and it involves only 2 extra lines of code. The problem I have
with it is this: if some fellow programmer is looking at my code in the future,
she may think: *"Hey, what's this unnecessary extra function call doing here?
It's probably some remnant of the past."* And she routinely rewrites it (back) to::

    @hookimpl
    async def get_some_awaitable():
        ...  # Do something

confident that she won't break anything, because this new code is semantically
exactly the same as the original, right? Only to find out, after hours of
debugging, that ``aiopluggy``'s built-in autodetection has ruined her day.

For this reason, ``aiopluggy`` provides the ``dont_await`` qualifier::

    @hookimpl.dont_await
    async def get_some_awaitable():
        ...  # Do something

Now, the special semantics are more explicit.


Hook specifications
-------------------
A *hook specification* is a definition used to validate each
*hook function* ensuring that an extension writer has correctly defined their
function *implementation*.

:class:`~aiopluggy.HookspecMarker` decorators are used to mark functions as *hook
specifications*. They work very similarly to :class:`~aiopluggy.HookimplMarker`
decorators, however only the function *signature* (its name and the names of its
arguments) is analyzed and stored. As such, often you will see a *hook
specification* with only a docstring in its body.

Just like a *plugin* is a set of hook *implementation* functions, hook
*specification* functions are grouped by namespaces, which are then fed to the
:class:`~aiopluggy.PluginManager` using the
:meth:`~aiopluggy.PluginManager.add_hookspecs()` method::

    from aiopluggy import HookspecMarker

    hookspec = HookspecMarker('my_project')

    @hookspec
    def send_greetings_to(name, address):
        """ Sends greetings to someone. """

    @hookspec
    def check_mail():
        """ See if there's a greeting for me. """

If the code-block above were in module :file:`greeting_specs.py`, you would do::

    from aiopluggy import PluginManager
    import greeting_specs

    pm = PluginManager('my_project')
    pm.add_hookspecs(greeting_specs)


Registering a *hook function* which does not meet the constraints of its
corresponding *hook specification* will result in an error.

.. note::

    A hook specification can also be added *after* some hook functions have been
    registered, and previously registered hook functions will still be
    validated. However this is not normally recommended.

Currently, ``aiopluggy`` supports two *hook specification qualifiers*:
:ref:`first_result` and ``replay``, which can *not* be combined.


.. _first_result:

``first_result``
^^^^^^^^^^^^^^^^
A *hookspec* can be marked such that when the *hook* is called the call loop
will only invoke up to the first *hookimpl* which returns a result other
then ``None``.

.. code-block:: python

    @hookspec.first_result
    def myhook(config, args):
        pass

This can be useful for optimizing a call loop for which you are only
interested in a single core *hookimpl*.


``replay``
^^^^^^^^^^
Marking a *hookspec* as with the ``replay`` qualifier means that calls to this
hook are remembered. When a new hook function is registered *after* the hook has
been called one or more times, these calls will be replayed to the newly
registered hook function. This turns out to be particularly useful when dealing
with lazy or dynamically loaded plugins::

    @hookspec.replay
    def initialize(config):
        pass

Late registered hook functions are called back immediately at register time.
This has two repercussions:

-   these hook functions *can not* return a result to the caller.
-   :meth:`PluginManager.register` returns a *future* that must be awaited,
    because some of the registered hook functions may be asynchronous.


More about namespaces
---------------------
As stated before, a *plugin implementation* is a *namespace* with *hook
functions*. Similarly, a *plugin specification* is a *namespace* of *hook
specifications*. However, *implementations* and *specifications* follow slightly
different rules, which are stated here:

*   A *plugin (implementation)* must be one of:

    *   a **module** with marked **module functions**
    *   a **class** with marked **class methods**
    *   an **instance object** with marked **instance methods**

*   A *plugin specification* must be one of:

    *   a **module** with marked **module functions**
    *   * **class** with marked **class methods** and **instance methods**


Enforcing specifications
------------------------
By default there is no strict requirement that each *hookimpl* has
a corresponding *hookspec*, or vice-versa. However, if you'd like you enforce this
behavior you can invoke the following methods:

:meth:`~aiopluggy.PluginManager.all_validated`:
    Returns ``True`` if there's a matching hook *specification* for each hook
    *function*.
:meth:`~aiopluggy.PluginManager.all_implemented`:
    Returns ``True`` if there's at least one hook *function* for each hook
    *specification*.


Opt-in arguments
----------------
To allow for *hookspecs* to evolve over the lifetime of a project,
*hookimpls* can accept **less** arguments then defined in the spec.
This allows for extending hook arguments (and thus semantics) without
breaking existing *hookimpls*.

In other words this is ok:

.. code-block:: python

    @hookspec
    def myhook(config, args):
        pass

    @hookimpl
    def myhook(args):
        print(args)


whereas this is not:

.. code-block:: python

    @hookspec
    def myhook(config, args):
        pass

    @hookimpl
    def myhook(config, args, extra_arg):
        print(args)


The Plugin Registry
-------------------
``aiopluggy`` manages plugins using instances of the
:class:`aiopluggy.PluginManager`.

A ``PluginManager`` is instantiated with a single
``str`` argument, the ``project_name``:

.. code-block:: python

    import aiopluggy
    pm = aiopluggy.PluginManager('my_project_name')


The ``project_name`` value is used when a ``PluginManager`` scans for *hook*
functions defined on a plugin. This allows for multiple
plugin managers from multiple projects to define hooks alongside each other.


.. _calling:

Calling Hooks
-------------
The core functionality of ``aiopluggy`` enables an extension provider
to override function calls made at certain points throughout a program.

A particular *hook* is invoked by calling an instance of
a :class:`aiopluggy.HookCaller` which in turn *loops* through the
``1:N`` registered *hookimpls* and calls them in sequence.

Every :class:`aiopluggy.PluginManager` has a ``hook`` attribute
which is an instance of this :class:`aiopluggy._HookRelay`.
The ``_HookRelay`` itself contains references (by hook name) to each
registered *hookimpl*'s ``HookCaller`` instance.

More practically you call a *hook* like so:

.. code-block:: python

    import sys
    import aiopluggy
    import mypluginspec
    import myplugin
    from configuration import config

    pm = aiopluggy.PluginManager("myproject")
    pm.add_hookspecs(mypluginspec)
    pm.register(myplugin)

    # we invoke the HookCaller and thus all underlying hookimpls
    result_list = pm.hook.myhook(config=config, args=sys.argv)

Note that you **must** call hooks using `keyword_arguments` syntax!

Hook implementations are called in LIFO registered order: *the last
registered plugin's hooks are called first*. As an example, the below
assertion should not error:

.. code-block:: python

    from aiopluggy import PluginManager, HookimplMarker

    hookimpl = HookimplMarker('myproject')

    class Plugin1(object):
        def myhook(self, args):
            """Default implementation.
            """
            return 1

    class Plugin2(object):
        def myhook(self, args):
            """Default implementation.
            """
            return 2

    class Plugin3(object):
        def myhook(self, args):
            """Default implementation.
            """
            return 3

    pm = PluginManager('myproject')
    pm.register(Plugin1())
    pm.register(Plugin2())
    pm.register(Plugin3())

    assert pm.hook.myhook(args=()) == [3, 2, 1]


Collecting results
^^^^^^^^^^^^^^^^^^
By default calling a hook results in all underlying hook functions to be invoked
in sequence via a loop. Any function which returns a value other then a ``None``
result will have that result appended to a :class:`list` which is returned by
the call.

The only exception to this behaviour is if the hook has been marked to return
its :ref:`first_result` in which case only the first single value (which is not
``None``) will be returned.

