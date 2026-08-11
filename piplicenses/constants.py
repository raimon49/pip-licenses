#!/usr/bin/env python
# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et
"""
pip-licenses

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

# Package constants
from . import (
    __pkgname__,  # noqa: F401 -- Re-export as part of data API
    __version__,  # noqa: F401 -- Re-export as part of data API
    Sequence,
)
from re import (
    Pattern,
    compile,
)

__summary__ = (
    "Dump the software license list of Python packages installed with pip."
)


FIELD_NAMES: set[str] = {
    "Name",
    "Version",
    "License",
    "LicenseFile",
    "LicenseText",
    "NoticeFile",
    "NoticeText",
    "Author",
    "Maintainer",
    "Description",
    "URL",
}


# Mapping of FIELD_NAMES to METADATA_KEYS where they differ by more than case
FIELDS_TO_METADATA_KEYS: dict[str, str] = {
    "URL": "home-page",
    "Description": "summary",
    "License-Metadata": "license",
    "License-Classifier": "license_classifier",
    "License-Expression": "license_expression",
}


# Placeholder for dynamic field names added in v6 (e.g., plural)

# unordered set (sorting should be done at output based on configuration)
SUMMARY_FIELD_NAMES: set[str] = {
    "Count",
    "License",
}


# Morally, this should be typed as an ordered-set
DEFAULT_OUTPUT_FIELDS: Sequence[str] = ("Name", "Version")


SUMMARY_OUTPUT_FIELDS: set[str] = {
    "Count",
    "License",
}


PEP735_URL_KEY = "Project-URL"
"""The PEP 753 `Project-URL` metadata key."""


# fall back to deprecated Core Metadata 1.0
# https://packaging.python.org/en/latest/specifications/core-metadata/#home-page
FALLBACK_URL_KEY = "home-page"
"""The (non PEP 753) `home-page` fallback metadata key."""


KNOWN_URL_SUB_KEYS = (
    # start with Core Metadata 1.2 (PEP 753)
    # https://packaging.python.org/en/latest/specifications/core-metadata/#core-metadata-project-url
    "homepage",
    # if all else fails, try alternative Core Metadata 1.2 labels
    # https://packaging.python.org/en/latest/specifications/well-known-project-urls/#well-known-labels
    "source",
    "repository",
    "changelog",
    "documentation",
    "bug tracker",
    )


PATTERN_DELIMITER: Pattern = compile(r"[-_.]+")
"""See here: https://peps.python.org/pep-0503/#normalized-names"""


# from PEP-440
VERSION_PATTERN = r"""
    v?
    (?:
        (?:(?P<epoch>[0-9]+)!)?                           # epoch
        (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?P<pre>                                          # pre-release
            [-_\.]?
            (?P<pre_l>alpha|a|beta|b|preview|pre|c|rc)
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>                                         # post release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                [-_\.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>                                          # dev release
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
    (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
"""


# morally these placeholders should be falsey
LICENSE_UNKNOWN: str = "UNKNOWN"
"""Placeholder when the license is undetermined"""

# Morally, this should be typed as a path-like string
FILE_MISSING: str = ""
"""Placeholder when the license file(s) is/are undetermined"""


LEGACY_LICENSE_BY_FILE_PATTERN = r"""[Ll][Ii][Cc][Ee][Nn][CScs][Ee].*|[Cc][Oo][Pp][Yy][Ii][Nn][Gg].*"""

# morally this is a glob (not a regex pattern)
LEGACY_NOTICE_BY_FILE_PATTERN = r"""NOTICE.*"""


LEGACY_AUTHORS_BY_FILE_PATTERN = r"""[Aa][Uu][Tt][Hh][Oo][Rr][Ss].*"""

# TODO: [GHI-394](https://github.com/raimon49/pip-licenses/issues/349)
LICENSE_BY_OTHER_FILE_PATTERN = r"[Aa][Uu][Tt][Hh][Oo][Rr][Ss].*|[Cc][Oo][Pp][Yy][Ii][Nn][Gg].*|[Ll][Ee][Gg][Aa][Ll].*"

# placeholder for classifier keys
