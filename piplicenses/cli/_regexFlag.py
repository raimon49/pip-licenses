# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et

# pip-licenses.cli._search_config
#
# MIT License
#
# Copyright (c) 2018-2025 raimon
# Copyright (c) 2025-2026 Mr. Walls
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


"""Enumerated regular expressions.

This is not part of the public API.

See [GHI-360](https://github.com/raimon49/pip-licenses/issues/360).
"""

import re
from enum import (
    Flag,
    auto,
)
# See https://github.com/raimon49/pip-licenses/issues/360
# should just bridge this import
from collections.abc import Iterable

# See https://github.com/raimon49/pip-licenses/issues/360
_PATTERN_TYPE = type(re.compile("", re.VERBOSE))
"""Not part of the public API."""

_RESERVED_INVALID_PATTERN: re.Pattern = re.compile(r"(?!)")
"""This should be an unmatchable pattern.

Not part of the public API. Subject to sudden changes, or removal.
"""


def _is_pattern(value: object) -> bool:
    """Return whether value is exactly a compiled regular expression."""
    return type(value) is _PATTERN_TYPE


class RegexFlag(Flag):
    """A Flag whose members each contain a regular expression."""

    def __new__(cls, value: int, pattern: re.Pattern):
        if not _is_pattern(pattern):
            raise TypeError(
                "pattern must be an instance of type re.Pattern"
            )
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, value: int, pattern: re.Pattern):
        self.pattern = pattern

    @property
    def regex(self) -> re.Pattern:
        members = tuple(self)

        if not members:
            return _RESERVED_INVALID_PATTERN

        return RegexFlag._any_regex_helper(*[member.pattern for member in members])

    @staticmethod
    def _any_regex_helper(*patterns: Iterable[re.Pattern]) -> re.Pattern:
        """Work around for defining combo values in subclasses.

        Because tuples do not allow `|` joining combo definitions need a workaround.
        Use like so:

        >>> class subRegexFlag(RegexFlag):
        ...    WORDS = 1, re.compile(r"(\\w+)")
        ...    DIGETS = 2, re.compile(r"(\\d*\\.?\\d+)")
        ...    BOTH = (1 | 2), RegexFlag._any_regex_helper(re.compile(r"(\\w+)"), re.compile(r"(\\d*\\.?\\d+)"))
        ...
        >>>

        """
        if not patterns:
            return _RESERVED_INVALID_PATTERN

        if not all(_is_pattern(pattern) for pattern in patterns):
            # loop through to find next non-pattern
            for _pattern in patterns:
                if not _is_pattern(_pattern):
                    raise TypeError(
                        "All patterns must be instances of type re.Pattern; "
                        f"'{str(_pattern)}' with type {type(_pattern)} is NOT {_PATTERN_TYPE}!"
                    )

        flags = {pattern.flags for pattern in patterns}
        if len(flags) != 1:
            raise ValueError("all patterns must use the same regex flags")

        expression = "|".join(
            f"(?:{pattern.pattern})"
            for pattern in patterns
        )
        return re.compile(expression, flags=patterns[0].flags)


__all__ = [
    """RegexFlag""",
]
