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

# See https://github.com/raimon49/pip-licenses/issues/360
# should just bridge this import
from collections.abc import Iterable
from enum import (
    Flag,
)

# See https://github.com/raimon49/pip-licenses/issues/360
_PATTERN_TYPE = type(re.compile("", re.VERBOSE))
"""Not part of the public API."""

_RESERVED_INVALID_PATTERN: re.Pattern = re.compile(r"(?!)")
"""This should be an unmatchable pattern.

Not part of the public API. Subject to sudden changes, or removal.
"""


# See https://github.com/raimon49/pip-licenses/issues/360
# morally this is a special boolean of typing.TypeIs[re.Pattern] but that requires python3.13+
# see typing.TypeIs
def _is_pattern(value: object) -> bool:
    """Return whether value is exactly a compiled regular expression."""
    return type(value) is _PATTERN_TYPE


class RegexFlags(Flag):
    """A Flag whose members each contain a regular expression.

    See also re.RegexFlag (not to be confused with)
    """

    def __new__(  # noqa: PYI034 -- typing.Self not appropriate for enums and Flags
        # see also https://github.com/astral-sh/ruff/issues/20781
        cls,
        value: int,
        pattern: re.Pattern,
    ) -> "RegexFlags":
        if not _is_pattern(pattern):
            raise TypeError("pattern must be an instance of type re.Pattern")
        obj = object.__new__(cls)  # see PYI034
        obj._value_ = value
        return obj

    def __init__(self, value: int, pattern: re.Pattern) -> None:
        self.pattern = pattern

    @property
    def regex(self) -> re.Pattern:
        members: Iterable = tuple(self)  # type: ignore[arg-type]

        if not members:
            return _RESERVED_INVALID_PATTERN

        return RegexFlags._any_regex_helper(
            *[member.pattern for member in members]
        )

    def __format__(self, format_spec: str) -> str:
        return self.regex.pattern.__format__(format_spec)

    def __str__(self) -> str:
        return (
            str(self.regex.pattern)
            if self.regex != _RESERVED_INVALID_PATTERN
            else ""
        )

    def __repr__(self) -> str:
        _name = f".{self._name_}" if self._name_ else ""
        _pattern = (
            f"; regex={self.regex.pattern}"
            if self.regex != _RESERVED_INVALID_PATTERN
            else ""
        )
        return f"<piplicenses.RegexFlags{_name} object{_pattern}>"

    @staticmethod
    def _any_regex_helper(*patterns: re.Pattern) -> re.Pattern:
        """Work around for defining combo values in subclasses.

        Because tuples do not allow `|` joining combo definitions need a workaround.
        Use like so:

        >>> class subRegexFlags(RegexFlags):
        ...    WORDS = 1, re.compile(r"(\\w+)")
        ...    DIGETS = 2, re.compile(r"(\\d*\\.?\\d+)")
        ...    BOTH = (1 | 2), RegexFlags._any_regex_helper(re.compile(r"(\\w+)"), re.compile(r"(\\d*\\.?\\d+)"))
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
                        f"'{str(_pattern)}' with type {type(_pattern)} is NOT {_PATTERN_TYPE}!"  # noqa: RUF010 -- handle classes with custom __format__ overloading with str() instead
                    )

        # Note: once again...
        # mypy (v1.19.1 for Python v3.9) is brain dead and thinks Patterns (the class) has no flags:
        # e.g., mypy struggles with this concept:
        #
        # >>> import re
        # >>> this_works = [example.flags for example in [re.compile(r"anything", re.VERBOSE)]][0]
        # >>> this_works
        # 96
        # >>> does_this_work = re.compile("anything", this_works)
        # >>> does_this_work
        # re.compile('anything', re.VERBOSE)
        #
        # so we need to ignore attr-defined here:
        flags = {pattern.flags for pattern in patterns}  # type: ignore[attr-defined]
        if len(flags) != 1:
            raise ValueError("all patterns must use the same regex flags")
        # and again here...
        expression = "|".join(f"(?:{pattern.pattern})" for pattern in patterns)  # type: ignore[attr-defined]
        # and again here...
        return re.compile(expression, flags=patterns[0].flags)  # type: ignore[attr-defined]


__all__ = [
    """RegexFlags""",
]
