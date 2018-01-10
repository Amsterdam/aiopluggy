0.1.3 First public release
--------------------------

Changes since Pluggy:

*   Made everything asynchronous.
*   Removed deprecated code, including the legacy ``__multicall__`` parameter
    handling.
*   Renamed from **pluggy** to **aiopluggy**
*   Removed compatibility with Python versions before 3.5.
*   Updated documentation.
*   Stripped much of the original CI stuff (tox, travis-ci) because I was in a
    hurry to get some MVP running. Will probably be re-introduced later.
*   Stripped some of the less-frequently used parts of the API, including:

    *   the many hook-2-plugin, plugin-2-name, name-2-plugin, plugin-2-hooks
        translators in `PluginManager`;
    *   plugin unloading.


0.1.0
-----

.. contributors
.. _@hpk42: https://github.com/hpk42
.. _@tgoodlet: https://github.com/tgoodlet
.. _@MichalTHEDUDE: https://github.com/MichalTHEDUDE
.. _@vodik: https://github.com/vodik
.. _@RonnyPfannschmidt: https://github.com/RonnyPfannschmidt
.. _@blueyed: https://github.com/blueyed
.. _@nicoddemus: https://github.com/nicoddemus
.. _@mdboom: https://github.com/mdboom
.. _@pieterb: https://github.com/pieterb
