# -*- coding: utf-8 -*-
# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et
"""
pip-licenses

MIT License

Copyright (c) 2018 raimon

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
from setuptools import setup, find_packages
from codecs import open
from os import path

from piplicenses import (__pkgname__ as PKG_NAME, __version__ as VERSION,
                         __author__ as AUTHOR, __license__ as LICENSE,
                         __summary__ as SUMMARY, __url__ as URL)


here = path.abspath(path.dirname(__file__))


def read_file(filename):
    content = ''
    with open(path.join(here, filename), encoding='utf-8') as f:
        content = f.read()

    return content


LONG_DESC = ''
try:
    from pypandoc import convert

    about_this = convert('README.md', 'rst', format='markdown_github')
    separate = '\n\n'
    change_log = convert('CHANGELOG.md', 'rst', format='markdown_github')

    LONG_DESC = about_this + separate + change_log
except (IOError, ImportError):
    LONG_DESC = read_file('README.md')


TEST_DEPENDS = [
    'pytest-cov',
    'pytest-pycodestyle',
    'pytest-runner',
]


setup(
    name=PKG_NAME,
    version=VERSION,
    description=SUMMARY,
    long_description=LONG_DESC,
    url=URL,
    author=AUTHOR,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: System Shells',
    ],
    keywords='pip pypi package license check',
    py_modules=['piplicenses'],
    license=LICENSE,
    install_requires=['PTable'],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=TEST_DEPENDS,
    extras_require={
        'test': TEST_DEPENDS,
    },
    entry_points={
        'console_scripts': [
            PKG_NAME + '=piplicenses:main',
        ],
    },
)
