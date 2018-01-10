#!/usr/bin/env python
""" See <https://setuptools.readthedocs.io/en/latest/>.
"""

from setuptools import setup


with open('README.rst') as fd:
    long_description = fd.read()


tests_require = [
    'pytest',
    'pytest-asyncio',
    'pytest-cov',
    'pytest-benchmark'
]


setup(
    name='aiopluggy',
    description='plugin and hook calling mechanisms for python',
    long_description=long_description,
    version='0.1.3-rc1',
    license='MIT license',
    platforms=['unix', 'linux', 'osx', 'win32'],
    author='Holger Krekel',
    author_email='holger@merlinux.eu',
    url='https://github.com/pieterb/aiopluggy',
    # python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ] + [
        ('Programming Language :: Python :: %s' % x)
        for x in '3.5 3.6'.split()
    ],
    setup_requires=['pytest-runner'],
    tests_require=tests_require,
    packages=['aiopluggy'],
    python_requires='~=3.6',
    extras_require={
        'docs': [
            'Sphinx',
            'sphinx-autobuild',
            'sphinx-autodoc-typehints',
            'sphinx_rtd_theme',
        ],
        'test': tests_require
    }
)
