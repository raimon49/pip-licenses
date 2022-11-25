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

from codecs import open
from os import path

from setuptools import setup

from piplicenses import __author__ as AUTHOR
from piplicenses import __license__ as LICENSE
from piplicenses import __pkgname__ as PKG_NAME
from piplicenses import __summary__ as SUMMARY
from piplicenses import __url__ as URL
from piplicenses import __version__ as VERSION

here = path.abspath(path.dirname(__file__))


def read_file(filename):
    content = ""
    with open(path.join(here, filename), encoding="utf-8") as f:
        content = f.read()

    return content


LONG_DESC = ""
try:
    from pypandoc import convert_file

    about_this = convert_file("README.md", "rst", format="markdown_github")
    separate = "\n\n"
    change_log = convert_file("CHANGELOG.md", "rst", format="markdown_github")

    LONG_DESC = about_this + separate + change_log
except (IOError, ImportError):
    LONG_DESC = read_file("README.md")


setup(
    name=PKG_NAME,
    version=VERSION,
    description=SUMMARY,
    long_description=LONG_DESC,
    url=URL,
    author=AUTHOR,
    license=LICENSE,
    entry_points={
        "console_scripts": [
            PKG_NAME + "=piplicenses:main",
        ],
    },
)
