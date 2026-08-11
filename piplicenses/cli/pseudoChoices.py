#!/usr/bin/env python
# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et
"""
pip-licenses.cli.pseudoChoices

MIT License

Copyright (c) 2018-2025 raimon
Copyright (c) 2025-2026 Mr. Walls

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

from . import (
    __pkgname__,  # noqa: F401 -- Re-export as part of __main__ API
    __version__,  # noqa: F401 -- Re-export as part of __main__ API
    annotations,  # noqa: F401 -- from piplicenses.__future__ -> piplicenses.cli
    TYPE_CHECKING,  # noqa: F401 -- Re-export as part of our internal typing API
# pseudoChoices does not seem to use annotations,
)


from enum import (
    Enum,
    auto,
)


class NoValueEnum(Enum):
    def __repr__(self) -> str:  # pragma: no cover
        return f"<{self.__class__.__name__}.{self.name}>"


class FromArg(NoValueEnum):
    META = M = auto()
    CLASSIFIER = C = auto()
    MIXED = MIX = auto()
    EXPRESSION = EXPR = auto()
    ALL = auto()


class OrderArg(NoValueEnum):
    COUNT = C = auto()
    LICENSE = L = auto()
    NAME = N = auto()
    AUTHOR = A = auto()
    MAINTAINER = M = auto()
    URL = U = auto()


class FormatArg(NoValueEnum):
    PLAIN = P = auto()
    PLAIN_VERTICAL = auto()
    MARKDOWN = MD = M = auto()
    RST = REST = R = auto()
    CONFLUENCE = C = auto()
    HTML = H = auto()
    JSON = J = auto()
    JSON_LICENSE_FINDER = JLF = auto()
    CSV = auto()


def value_to_enum_key(value: str) -> str:
    return value.replace("-", "_").upper()


def enum_key_to_value(enum_key: Enum) -> str:
    return enum_key.name.replace("_", "-").lower()


def choices_from_enum(enum_cls: type[NoValueEnum]) -> list[str]:
    return [key.replace("_", "-").lower() for key in enum_cls.__members__]


def get_value_from_enum(
    enum_cls: type[NoValueEnum], value: str
) -> NoValueEnum:
    return getattr(enum_cls, value_to_enum_key(value))
