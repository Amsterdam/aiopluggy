.. _index:

aiopluggy
=========
``aiopluggy`` is a plugin manager for (partially) asynchronous plugins in an
asynchronous application. For example, it allows you to write an `aiohttp`_
service with a pluggable storage back-end, and a set of asynchronous plugins for
MySQL, SQLServer, Postgres etcetera. In essence, ``aiopluggy`` enables function
`hooking`_ so you can build "pluggable" systems.

``aiopluggy`` reuses much of the code in `pluggy`_, the plugin manager used by
`pytest`_.


Table of Contents
-----------------
.. toctree::

    tutorial
    api_reference
    todo_list
    genindex


.. hyperlinks
.. _pytest:
    http://pytest.org
.. _pluggy:
    https://pluggy.readthedocs.io/en/latest/
.. _aiohttp:
    https://aiohttp.readthedocs.io/en/latest/
.. _hooking:
    https://en.wikipedia.org/wiki/Hooking
