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


"""File search configuration model for granular control of file search heuristics.

See [GHI-375](https://github.com/raimon49/pip-licenses/issues/375) for full design rationale.

PROTOTYPE; This component will move to a pip-licenses.config.??? in the future!
Do not rely on this component prior to v6.2;
see [GHI-375](https://github.com/raimon49/pip-licenses/issues/81) for integration details.
"""

import re

from .. import LEGACY_LICENSE_BY_FILE_PATTERN
from ._regex_flag import (
    _RESERVED_INVALID_PATTERN,  # the regex
    RegexFlags,  # the class
)
from .config import Configuration

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

    WITHOUT_FILES = (
        0,
        _RESERVED_INVALID_PATTERN,
    )  # no search
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


def getRegexForExtraFiles(args: Configuration) -> ExtraFilesRegex:
    r"""Select the filename-search regex from the configured file and path toggles.

    This helper decides which *extra-file categories* to search. It does not
    decide whether matching file contents or paths are included in output;
    those are separate format choices. In particular, the category toggles
    select licenses, legacy files, notices, authors, or attributions, while
    ``with_others``, ``with_other_files``, and ``with_other_paths`` enable
    the catch-all extra-file search. The ``without_*`` overrides remove
    categories from that catch-all or from the individually selected set.

    This reflects the v6 flag design discussed in
    `GHI-375 <https://github.com/raimon49/pip-licenses/issues/375>`_:
    file contents and paths are independently configurable, and “other files”
    refers to heuristic discovery beyond metadata-listed files.

    Args:
        args: Configuration-like object providing the file and path toggles
            consulted by this helper. A falsey value selects no extra files.

    Returns:
        The ``ExtraFilesRegex`` flag whose combined regular expression matches
        the selected filename categories. ``WITHOUT_FILES`` has no matches.

    Examples:
        >>> from types import SimpleNamespace
        >>> from piplicenses.cli._search_config import (
        ...     ExtraFilesRegex,
        ...     getRegexForExtraFiles,
        ... )
        >>> _fields = (
        ...     "with_others", "with_other_files", "with_other_paths",
        ...     "without_files", "without_paths",
        ...     "without_authors_files", "without_authors_paths",
        ...     "without_notice_files", "without_notice_paths",
        ...     "without_attribution_files", "without_attribution_paths",
        ...     "without_legacy_files", "without_legacy_paths",
        ...     "with_license_files", "with_license_paths",
        ...     "with_legacy_files", "with_legacy_paths",
        ...     "with_authors_files", "with_authors_paths",
        ...     "with_notice_files", "with_notice_paths",
        ...     "with_attribution_files", "with_attribution_paths",
        ...     "with_files", "with_paths", "with_authors",
        ...     "with_maintainers", "with_notices",
        ...     "without_license_files", "without_license_paths",
        ... )
        >>> def select(**overrides):
        ...     values = dict.fromkeys(_fields, False)
        ...     values.update(overrides)
        ...     return getRegexForExtraFiles(SimpleNamespace(**values))
        >>> getRegexForExtraFiles(None) is ExtraFilesRegex.WITHOUT_FILES
        True
        >>> select().value
        0

    The license, legacy, author, notice, and attribution toggles select their
    corresponding categories. License file *or* path toggles select both
    license filename patterns; legacy file *or* path toggles select the
    combined legacy category. Attribution is selected only when both of its
    file and path toggles are true.

        >>> select(with_license_files=True).value
        3
        >>> select(with_license_paths=True).value
        3
        >>> select(with_legacy_files=True).value
        18
        >>> select(with_legacy_paths=True).value
        18
        >>> select(with_authors_files=True).value
        8
        >>> select(with_authors_paths=True).value
        8
        >>> select(with_notice_files=True).value
        4
        >>> select(with_notice_paths=True).value
        4
        >>> select(with_attribution_files=True, with_attribution_paths=True).value
        40
        >>> select(with_attribution_files=True).value
        0
        >>> select(with_attribution_paths=True).value
        0

    ``with_files`` and ``with_paths`` together add the general license-like
    search, and can opt into authors, maintainer attributions, and notices.
    Their paired ``without_*`` overrides suppress those additions. The
    license-file suppression also removes the license categories selected by
    this general search.

        >>> select(with_files=True, with_paths=True).value
        2
        >>> select(with_files=True, with_paths=True, with_authors=True).value
        10
        >>> select(with_files=True, with_paths=True, with_maintainers=True).value
        42
        >>> select(with_files=True, with_paths=True, with_authors=True,
        ...        without_authors_files=True, without_authors_paths=True).value
        2
        >>> select(with_files=True, with_paths=True, with_notices=True).value
        6
        >>> select(with_files=True, with_paths=True, with_notices=True,
        ...        without_notice_files=True, without_notice_paths=True).value
        2
        >>> select(with_files=True, with_paths=True, with_maintainers=True,
        ...        without_attribution_files=True,
        ...        without_attribution_paths=True).value
        10
        >>> select(with_files=True, with_paths=True,
        ...        without_license_files=True,
        ...        without_license_paths=True).value
        0

    Any of the three catch-all toggles starts with every extra category.
    Paired ``without_*`` overrides then subtract their categories. In
    particular, the attribution override removes both authors and
    attribution patterns, while the general files-and-paths override also
    removes the license and reserved legacy categories.

        >>> select(with_others=True).value
        127
        >>> select(with_other_files=True).value
        127
        >>> select(with_other_paths=True).value
        127
        >>> select(with_others=True, without_authors_files=True,
        ...        without_authors_paths=True).value
        119
        >>> select(with_others=True, without_notice_files=True,
        ...        without_notice_paths=True).value
        123
        >>> select(with_others=True, without_attribution_files=True,
        ...        without_attribution_paths=True).value
        87
        >>> select(with_others=True, without_legacy_files=True,
        ...        without_legacy_paths=True).value
        111
        >>> select(with_others=True, without_files=True, without_paths=True,
        ...        without_authors_files=True, without_authors_paths=True,
        ...        without_notice_files=True, without_notice_paths=True,
        ...        without_attribution_files=True,
        ...        without_attribution_paths=True,
        ...        without_legacy_files=True, without_legacy_paths=True).value
        64
        >>>

    The returned flag exposes the combined compiled pattern through
    ``.regex``. These examples check representative matches and non-matches
    for the selected categories, including case-insensitive filenames and
    common extensions.

        >>> _license_regex = select(with_license_files=True).regex
        >>> bool(_license_regex.search("LiCeNsE.md"))
        True
        >>> bool(_license_regex.search("LICENSE-custom.txt"))
        False
        >>> bool(_license_regex.search("NOTICE"))
        False

        >>> _legacy_regex = select(with_legacy_paths=True).regex
        >>> bool(_legacy_regex.search("COPYING.txt"))
        True
        >>> bool(_legacy_regex.search("COPYING.LESSER"))
        False
        >>> bool(_legacy_regex.search("LICENSE.json"))
        True
        >>> bool(_legacy_regex.search("LICENSE-MIT"))
        False
        >>> bool(_legacy_regex.search("AUTHORS"))
        False

        >>> _authors_regex = select(with_authors_files=True).regex
        >>> bool(_authors_regex.search("AUTHORS.txt"))
        True
        >>> bool(_authors_regex.search("CONTRIBUTORS"))
        False

        >>> _notice_regex = select(with_notice_paths=True).regex
        >>> bool(_notice_regex.search("NOTICE.rst"))
        True
        >>> bool(_notice_regex.search("NOTICE.json"))
        False
        >>> bool(_notice_regex.search("AUTHORS"))
        False

        >>> _attributions_regex = select(
        ...     with_attribution_files=True,
        ...     with_attribution_paths=True,
        ... ).regex
        >>> bool(_attributions_regex.search("CONTRIBUTORS"))
        True
        >>> bool(_attributions_regex.search("ACKNOWLEDGMENTS.md"))
        True
        >>> bool(_attributions_regex.search("AUTHORS"))
        True
        >>> bool(_attributions_regex.search("NOTICE"))
        False

        >>> _others_regex = select(with_others=True).regex
        >>> all(
        ...     _others_regex.search(filename)
        ...     for filename in (
        ...         "LICENSE",
        ...         "LICENSE.txt",
        ...         "LICENSE.any",
        ...         "NOTICE",
        ...         "AUTHORS",
        ...         "COPYING.txt",
        ...         "CONTRIBUTORS",
        ...         "PATENTS.md",
        ...         "LEGAL.txt",
        ...     )
        ... )
        True
        >>> bool(_others_regex.search("README.md"))
        False

        >>> _no_files_regex = select().regex
        >>> _no_files_regex.search("LICENSE") is None
        True
        >>>

    """
    if not args:
        return ExtraFilesRegex.WITHOUT_FILES
    # first check if others is enabled:
    if args.with_others or (args.with_other_files or args.with_other_paths):
        # default to Others
        _regex = ExtraFilesRegex.EXTRA_OTHERS
        # so now just subtract remaining overrides:
        if args.without_files and args.without_paths:
            # then assume just others
            _regex &= ~ExtraFilesRegex.EXTRA_FILES
            _regex &= ~ExtraFilesRegex.EXTRA_LICENSES
            _regex &= ~ExtraFilesRegex.RESERVED_LEGACY
        if args.without_authors_files and args.without_authors_paths:
            # then omit author files
            _regex &= ~ExtraFilesRegex.EXTRA_AUTHORS
        if args.without_notice_files and args.without_notice_paths:
            # then omit notices
            _regex &= ~ExtraFilesRegex.EXTRA_NOTICES
        if args.without_attribution_files and args.without_attribution_paths:
            # then omit attributions (including authors)
            _regex &= ~ExtraFilesRegex.EXTRA_ATTRIBUTIONS
        if args.without_legacy_files and args.without_legacy_paths:
            # then omit legacy
            _regex &= ~ExtraFilesRegex.RESERVED_LEGACY
        return _regex
    else:
        # default to Others
        _regex = ExtraFilesRegex.WITHOUT_FILES
        if args.with_license_files or args.with_license_paths:
            _regex |= ExtraFilesRegex.EXTRA_FILES
            _regex |= ExtraFilesRegex.EXTRA_LICENSES
        if args.with_legacy_files or args.with_legacy_paths:
            # then include legacy
            _regex |= ExtraFilesRegex.EXTRA_LEGACY
        # NOTE: some of the combos here are not possible from the CLI because with/without flags
        # conflict and can not pass validate checks...
        if args.with_authors_files or args.with_authors_paths:
            # then include authors
            _regex |= ExtraFilesRegex.EXTRA_AUTHORS
        if args.with_notice_files or args.with_notice_paths:
            # ... but omit notice files if overridden
            _regex |= ExtraFilesRegex.EXTRA_NOTICES
        if args.with_attribution_files and args.with_attribution_paths:
            # ... but omit attribution files if overridden
            _regex |= ExtraFilesRegex.EXTRA_ATTRIBUTIONS
        if args.with_files and args.with_paths:
            # then add extras
            _regex |= ExtraFilesRegex.EXTRA_LICENSES
            if args.with_authors:
                # consider adding authors...
                _regex |= ExtraFilesRegex.EXTRA_AUTHORS
            if args.with_maintainers:
                # consider adding attribution...
                _regex |= ExtraFilesRegex.EXTRA_ATTRIBUTIONS
            if args.without_authors_files and args.without_authors_paths:
                # ... but omit author files if overridden
                _regex &= ~ExtraFilesRegex.EXTRA_AUTHORS
            if args.with_notices:
                # consider adding notices...
                _regex |= ExtraFilesRegex.EXTRA_NOTICES
            if args.without_notice_files and args.without_notice_paths:
                # ... but omit notice files if overridden
                _regex &= ~ExtraFilesRegex.EXTRA_NOTICES
            if (
                args.without_attribution_files
                and args.without_attribution_paths
            ):
                # ... but omit attribution files if overridden
                _regex &= ~ExtraFilesRegex.RESERVED_ATTRIBUTIONS
        if args.without_license_files and args.without_license_paths:
            # ... but omit licenses files if overridden
            _regex &= ~ExtraFilesRegex.EXTRA_FILES
            _regex &= ~ExtraFilesRegex.EXTRA_LICENSES
        return _regex
    return ExtraFilesRegex.WITHOUT_FILES


__all__ = [
    "ExtraFilesRegex",
    # TODO: before version 6.2.x should also export getRegexForExtraFiles
]
