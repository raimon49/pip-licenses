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


"""File search configuration model for granular control of file/path/content output.

This module implements the S.O.L.I.D.-aligned configuration model that separates:
1. File category selection (what to search)
2. Representation preferences (how to emit results)
3. Category-specific suppressions (selective disabling)
4. Provenance tracking (explicit vs. aggregate vs. inherited)

See [GHI-375](https://github.com/raimon49/pip-licenses/issues/375) for full design rationale.
"""

import re
from dataclasses import (
    dataclass,
    field,
)
from enum import (
    Enum,
    Flag,
    auto,
)
from ._regexFlag import RegexFlag  # the class
from .. import LEGACY_LICENSE_BY_FILE_PATTERN

_RESERVED_BY_FILE_PATTERN: re.Pattern = re.compile(
    r"^(?:[Ll][Ii][Cc][Ee][Nn][CScs][Ee])(?:\.(?:(?:(?:(?:[Tt][Xx])|(?:[Rr][Ss]))[Tt])|(?:[Mm][Dd])))?$",
    re.UNICODE | re.MULTILINE | re.VERBOSE,
)
"""Not part of the public API."""

_NOTICE_BY_FILE_PATTERN: re.Pattern = re.compile(
    r"^(?:[Nn][Oo][Tt][Ii][Cc][Ee])(?:\.(?:(?:(?:(?:[Tt][Xx])|(?:[Rr][Ss]))[Tt])|(?:[Mm][Dd])))?$",
    re.UNICODE | re.MULTILINE | re.VERBOSE,
)
"""Not part of the public API."""

_AUTHORS_BY_FILE_PATTERN: re.Pattern = re.compile(
    r"^(?:[Aa][Uu][Tt][Hh][Oo][Rr][Ss])(?:\.(?:(?:(?:(?:[Tt][Xx])|(?:[Rr][Ss]))[Tt])|(?:[Mm][Dd])))?$",
    re.UNICODE | re.MULTILINE | re.VERBOSE,
)
"""Not part of the public API."""

_ATTRIBUTIONS_BY_FILE_PATTERN: re.Pattern = re.compile(
    r"^(?:(?:[Cc][Oo][Nn][Tt][Rr][Ii][Bb][Uu][Tt][Oo][Rr][Ss]?)|(?:[Cc][Rr][Ee][Dd][Ii][Tt][Ss]?)|(?:[Aa][Cc][Kk][Nn][Oo][Ww][Ll][Ee][Dd][Gg][Mm][Ee][Nn][Tt][Ss])|(?:[Aa][Tt]{2}[Rr][Ii][Bb][Uu][Tt][Ii][Oo][Nn][Ss]?))(?:\.(?:(?:(?:(?:[Tt][Xx])|(?:[Rr][Ss]))[Tt])|(?:[Mm][Dd])))?$",
    re.UNICODE | re.MULTILINE | re.VERBOSE,
)
"""Not part of the public API."""

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
        _RESERVED_BY_FILE_PATTERN, _NOTICE_BY_FILE_PATTERN,
        _AUTHORS_BY_FILE_PATTERN, _EXTRA_LEGACY_BY_FILE_PATTERN,
        _ATTRIBUTIONS_BY_FILE_PATTERN, _OTHER_RESERVED_BY_FILE_PATTERN,
    ]
"""Not part of the public API."""


class ExtraFilesCategory(RegexFlag):
    """Enumeration of all extra file discovery categories with search regex."""
    EXTRA_FILES = 1, _RESERVED_BY_FILE_PATTERN  # Heuristic search for LICENSE-like files
    EXTRA_NOTICES = 2, _NOTICE_BY_FILE_PATTERN  # Heuristic search for NOTICE-like files
    EXTRA_AUTHORS = 4, _AUTHORS_BY_FILE_PATTERN  # Heuristic search for AUTHORS-like files
    EXTRA_ATTRIBUTIONS = 16, RegexFlag._any_regex_helper(*[_AUTHORS_BY_FILE_PATTERN, _ATTRIBUTIONS_BY_FILE_PATTERN])  # Heuristic search for ATTRIBUTION files; e.g., AUTHORS, CONTRIBUTORS, CREDITS, ACKNOWLEDGMENTS, ATTRIBUTION, etc.
    EXTRA_LEGACY = 8, _EXTRA_LEGACY_BY_FILE_PATTERN  # Heuristic search for LICENSE/COPYING files (not in metadata)
    EXTRA_RESERVED = 32, _OTHER_RESERVED_BY_FILE_PATTERN  # reserved for other extra files

    # Catch-all for other extra files
    EXTRA_OTHERS = (1 | 2 | 4 | 8 | 16 | 32), RegexFlag._any_regex_helper(*_COMBO_OTHER_PATTERN_LIST)


class FileCategory(Flag):
    """Enumeration of all file discovery categories."""

    # Derive paths from core metadata License-File
    METADATA_LICENSE = auto()  # From core metadata License-File
    # Include NOTICE-like paths from core metadata Project-File
    METADATA_NOTICE = auto()  # From core metadata (if added)

    # Heuristic searches for other paths
    EXTRA_AUTHORS = auto()  # Heuristic search for AUTHORS-like files
    EXTRA_ATTRIBUTION = auto()  # Heuristic search for ATTRIBUTION files
    EXTRA_NOTICES = auto()  # Heuristic search for NOTICE-like files
    EXTRA_LEGACY = auto()  # Heuristic search for LICENSE/COPYING (not in metadata)
    EXTRA_OTHER = auto()  # Catch-all for other extra files

    EXTRA_ALL = EXTRA_AUTHORS | EXTRA_ATTRIBUTION | EXTRA_NOTICES | EXTRA_LEGACY | EXTRA_OTHER


class Provenance(Enum):
    """Track how a flag was enabled: explicit CLI, aggregate, or inherited."""

    EXPLICIT = auto()  # User specified this flag directly
    AGGREGATE = auto()  # Enabled as part of a larger aggregate flag (e.g., --with-others)
    INHERITED = auto()  # Enabled as side effect of another flag


@dataclass
class CategoryState:
    """State for a single file category with provenance tracking.

    Attributes:
        enabled: Whether this category is eligible for searching.
        provenance: How this setting was determined.
        implied_by: Set of flags that caused this state (for diagnostics).
    """

    enabled: bool = False
    provenance: Provenance = Provenance.EXPLICIT
    implied_by: set[str] = field(default_factory=set)

    def __bool__(self) -> bool:
       """True only if flag is enabled, otherwise false."""
       return self.enabled is True

    def __repr__(self) -> str:
        """Provide clear diagnostic output."""
        implied_str = f" (implied by: {', '.join(sorted(self.implied_by))})" if self.implied_by else ""
        return f"CategoryState(enabled={self.enabled}, provenance={self.provenance.name}{implied_str})"
