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


"""File search configuration model for granular control of file content/path output.

See [GHI-375](https://github.com/raimon49/pip-licenses/issues/375) for full design rationale.

PROTOTYPE; This component will move to a pip-licenses.config.??? in the future!
Do not rely on this component prior to v6.2;
see [GHI-375](https://github.com/raimon49/pip-licenses/issues/81) for integration details.
"""

import re

# See https://github.com/raimon49/pip-licenses/issues/360
# should just bridge this import
# from collections.abc import Iterable
from enum import (
    Flag,
    auto,
)

from .. import LEGACY_LICENSE_BY_FILE_PATTERN
from ._argparse_bridge import argparse  # the module
from ._format_nomenclature import reduce_to_config_form  # the function
from ._regex_flag import RegexFlags  # the class

_RESERVED_BY_FILE_PATTERN: re.Pattern = re.compile(
    r"^(?:[Ll][Ii][Cc][Ee][Nn][CScs][Ee])(?:\.(?:(?:(?:(?:[Tt][Xx])|(?:[Rr][Ss]))[Tt])|(?:[Mm][Dd])))?$",
    re.UNICODE | re.MULTILINE | re.VERBOSE,
)
"""Not part of the public API.

Matches case-insensitive "LICENSE" or "LICENCE" (common misspelling) with an optional extension of
either ".md", ".rst", or ".txt".
"""

_EXTRA_LICENSES_BY_FILE_PATTERN: re.Pattern = re.compile(
    r"^(?:[Ll][Ii][Cc][Ee][Nn][CScs][Ee])(?:\..*)?$",
    re.UNICODE | re.MULTILINE | re.VERBOSE,
)
"""Not part of the public API.

Matches case-insensitive "LICENSE" or "LICENCE" (common misspelling) optionally with any extension.
"""

_NOTICE_BY_FILE_PATTERN: re.Pattern = re.compile(
    r"^(?:[Nn][Oo][Tt][Ii][Cc][Ee])(?:\.(?:(?:(?:(?:[Tt][Xx])|(?:[Rr][Ss]))[Tt])|(?:[Mm][Dd])))?$",
    re.UNICODE | re.MULTILINE | re.VERBOSE,
)
"""Not part of the public API.

Matches NOTICE-like files.
"""

_AUTHORS_BY_FILE_PATTERN: re.Pattern = re.compile(
    r"^(?:[Aa][Uu][Tt][Hh][Oo][Rr][Ss])(?:\.(?:(?:(?:(?:[Tt][Xx])|(?:[Rr][Ss]))[Tt])|(?:[Mm][Dd])))?$",
    re.UNICODE | re.MULTILINE | re.VERBOSE,
)
"""Not part of the public API.

Matches AUTHORS-like files.
"""

_ATTRIBUTIONS_BY_FILE_PATTERN: re.Pattern = re.compile(
    r"^(?:(?:[Cc][Oo][Nn][Tt][Rr][Ii][Bb][Uu][Tt][Oo][Rr][Ss]?)|(?:[Cc][Rr][Ee][Dd][Ii][Tt][Ss]?)|(?:[Aa][Cc][Kk][Nn][Oo][Ww][Ll][Ee][Dd][Gg][Mm][Ee][Nn][Tt][Ss])|(?:[Aa][Tt]{2}[Rr][Ii][Bb][Uu][Tt][Ii][Oo][Nn][Ss]?))(?:\.(?:(?:(?:(?:[Tt][Xx])|(?:[Rr][Ss]))[Tt])|(?:[Mm][Dd])))?$",
    re.UNICODE | re.MULTILINE | re.VERBOSE,
)
"""Not part of the public API.

Matches CONTRIBUTORS|CREDITS|ACKNOWLEDGMENTS|ATTRIBUTION like files.
"""

_LEGACY_RESERVED_BY_FILE_PATTERN: re.Pattern = re.compile(
    r"^(?:(?:[Cc][Oo][Pp][Yy][Ii][Nn][Gg]))(?:\.(?:(?:(?:(?:[Tt][Xx])|(?:[Rr][Ss]))[Tt])|(?:[Mm][Dd])))?$",
    re.UNICODE | re.MULTILINE | re.VERBOSE,
)
"""Not part of the public API.

Matches COPYING-like files.
"""

_OTHER_RESERVED_BY_FILE_PATTERN: re.Pattern = re.compile(
    r"^(?:(?:(?:[Pp][Aa][Tt][Ee][Nn][Tt][Ss]?)|(?:[Cc][Oo][Pp][Yy][Ii][Nn][Gg])|(?:[Ll][Ee][Gg][Aa][Ll])))(?:\.(?:(?:(?:(?:[Tt][Xx])|(?:[Rr][Ss]))[Tt])|(?:[Mm][Dd])))?$",
    re.UNICODE | re.MULTILINE | re.VERBOSE,
)
"""Not part of the public API."""

_EXTRA_LEGACY_BY_FILE_PATTERN: re.Pattern = re.compile(
    LEGACY_LICENSE_BY_FILE_PATTERN,
    re.UNICODE | re.MULTILINE | re.VERBOSE,
)
"""Not part of the public API."""

_COMBO_OTHER_PATTERN_LIST: list[re.Pattern] = [
    _RESERVED_BY_FILE_PATTERN,
    _EXTRA_LICENSES_BY_FILE_PATTERN,
    _NOTICE_BY_FILE_PATTERN,
    _AUTHORS_BY_FILE_PATTERN,
    _EXTRA_LEGACY_BY_FILE_PATTERN,
    _ATTRIBUTIONS_BY_FILE_PATTERN,
    _LEGACY_RESERVED_BY_FILE_PATTERN,
    _OTHER_RESERVED_BY_FILE_PATTERN,
]
"""Not part of the public API."""


class ExtraFilesRegex(RegexFlags):
    """Enumeration of all extra file discovery categories with search regex."""

    EXTRA_FILES = (
        1,
        _RESERVED_BY_FILE_PATTERN,
    )  # Heuristic search for LICENSE text files
    EXTRA_LICENSES = (
        2,
        _EXTRA_LICENSES_BY_FILE_PATTERN,
    )  # Heuristic search for LICENSE-like files
    EXTRA_NOTICES = (
        4,
        _NOTICE_BY_FILE_PATTERN,
    )  # Heuristic search for NOTICE-like files
    EXTRA_AUTHORS = (
        8,
        _AUTHORS_BY_FILE_PATTERN,
    )  # Heuristic search for AUTHORS-like files
    RESERVED_ATTRIBUTIONS = (
        32,
        _ATTRIBUTIONS_BY_FILE_PATTERN,
    )  # Heuristic search for just ATTRIBUTION files; e.g. CONTRIBUTORS, CREDITS, ACKNOWLEDGMENTS, ATTRIBUTION, etc.
    EXTRA_ATTRIBUTIONS = (
        (8 | 32),
        RegexFlags._any_regex_helper(
            *[_AUTHORS_BY_FILE_PATTERN, _ATTRIBUTIONS_BY_FILE_PATTERN]
        ),
    )  # Heuristic search for ATTRIBUTION files; e.g., AUTHORS, CONTRIBUTORS, CREDITS, ACKNOWLEDGMENTS, ATTRIBUTION, etc.
    RESERVED_LEGACY = (
        16,
        _LEGACY_RESERVED_BY_FILE_PATTERN,
    )  # Heuristic search for COPYING files (not in metadata)
    EXTRA_LEGACY = (
        (2 | 16),
        _EXTRA_LEGACY_BY_FILE_PATTERN,
    )  # Heuristic search for LICENSE/COPYING files (not in metadata)
    EXTRA_RESERVED = (
        64,
        RegexFlags._any_regex_helper(
            *[
                _LEGACY_RESERVED_BY_FILE_PATTERN,
                _OTHER_RESERVED_BY_FILE_PATTERN,
            ]
        ),
    )  # reserved for other extra files

    # Catch-all for other extra files
    EXTRA_OTHERS = (
        (1 | 2 | 4 | 8 | 16 | 32 | 64),
        RegexFlags._any_regex_helper(*_COMBO_OTHER_PATTERN_LIST),
    )


class FileFormat(Flag):
    """Enumeration of files format modes."""

    # Individually
    SHOW_CONTENTS = auto()  # Include file contents
    SHOW_PATHS = auto()  # Include file paths
    # Combos
    SHOW_BOTH = SHOW_CONTENTS | SHOW_PATHS
    # Negation
    SHOW_NONE = 0  # semantically: ~SHOW_BOTH


class FileCategory(Flag):
    """Enumeration of all file discovery categories."""

    # Include recognized paths from core metadata Project-File
    METADATA = auto()  # 1 E.g., any files
    # Derive paths from core metadata License-File
    LICENSE = auto()  # 2 From core metadata License-File
    # Heuristic searches for other paths
    OTHERS = auto()  # 4 Catch-all for other extra files
    AUTHORS = auto()  # 8 Heuristic search for AUTHORS-like files
    ATTRIBUTION = auto()  # 16 Heuristic search for ATTRIBUTION-like files
    NOTICES = auto()  # 32 Heuristic search for NOTICE-like files
    LEGACY = (
        auto()
    )  # 64 Heuristic search for LICENSE/COPYING (not in metadata)
    # Combos
    ANY = (
        AUTHORS | ATTRIBUTION | NOTICES | LEGACY | OTHERS
    )  # 124 (127 - 1+2) E.g., any other paths


_FORMAT_CATEGORIES: list[FileCategory] = [
    FileCategory.ATTRIBUTION,
    FileCategory.AUTHORS,
    FileCategory.LEGACY,
    FileCategory.LICENSE,
    FileCategory.NOTICES,
    FileCategory.OTHERS,
]
"""Internal list of file-format-able categories.

Not part of the public API.
"""


# See https://github.com/raimon49/pip-licenses/issues/360
# prefix_hint type could be literal[str] from:
# FORMAT_CATEGORIES[*].name.lower().strip('s')
#  + 'global'
#  + 'supports'
# note: fallback 'supports' is the only value that ends in an 's'
def _resolve_file_format(
    args: argparse.Namespace,
    *,
    prefix_hint: str = "supports",
    default: FileFormat = FileFormat.SHOW_NONE,
) -> FileFormat:
    """Internal helper for resolve_file_formats().

    Not part of the public API.
    """
    # see _format_nomenclature.FORMAT_OVERRIDE_FIELD
    contents = getattr(args, f"{prefix_hint}_files")
    paths = getattr(args, f"{prefix_hint}_paths")
    fmt = default
    if (contents is not None) and contents:
        fmt |= FileFormat.SHOW_CONTENTS
    if (paths is not None) and paths:
        fmt |= FileFormat.SHOW_PATHS
    return fmt


def resolve_file_formats(
    args: argparse.Namespace,
    *,
    default: FileFormat = FileFormat.SHOW_NONE,
) -> dict[FileCategory, FileFormat]:
    """
    Convert argparse's tri-state booleans into FileFormat values.

    An unspecified setting inherits `default`.
    """
    formats: dict[FileCategory, FileFormat] = {
        FileCategory.METADATA: _resolve_file_format(
            args=args,
            prefix_hint="supports",
            default=default,
        ),
    }
    for category in _FORMAT_CATEGORIES:
        if category.name:  # e.g., only handle named categories
            category_name: str = category.name.lower().strip("s")
            fmt = _resolve_file_format(
                args=args,
                prefix_hint=reduce_to_config_form(category_name),
                default=default,
            )
            formats[category] = fmt
        # else skip
    return formats


__all__ = [
    "ExtraFilesRegex",
    "FileCategory",
    "FileFormat",
    "resolve_file_formats",
]


# NOTE: this module intentionally keeps a small, explicit surface area.
# Patterns and category resolution are handled here; the argparse integration
# remains intentionally decoupled so that higher-level CLI validation can decide
# whether a format supports file contents before rendering them.
