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

from __future__ import annotations

import argparse
import codecs
import os
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Generator, Iterable, Iterator, Sequence
from enum import Enum, auto
from functools import partial
from io import open as _real_io_open
from pathlib import Path
from typing import TYPE_CHECKING, cast

from prettytable import HRuleStyle, PrettyTable, RowType

from .tomli_bridge import tomllib


__pkgname__ = "pip-licenses"
__version__ = "6.0.0b5"  # (dev-v6.0 branch)


from .constants import (
    __summary__,
    FIELD_NAMES,
    SUMMARY_FIELD_NAMES,
    DEFAULT_OUTPUT_FIELDS,
    SUMMARY_OUTPUT_FIELDS,
    PEP735_URL_KEY,
    FALLBACK_URL_KEY,
    KNOWN_URL_SUB_KEYS,
    PATTERN_DELIMITER,
    VERSION_PATTERN,
    LICENSE_UNKNOWN,
    FILE_MISSING,
    LEGACY_LICENSE_BY_FILE_PATTERN,
    LEGACY_NOTICE_BY_FILE_PATTERN,
    LEGACY_AUTHORS_BY_FILE_PATTERN,
    LICENSE_BY_OTHER_FILE_PATTERN,
)


def normalize_pkg_name(pkg_name: str) -> str:
    """Return normalized name according to PEP specification

    See here: https://peps.python.org/pep-0503/#normalized-names

    Args:
        pkg_name: Package name it is extracted from the package metadata
                  or specified in the CLI

    Returns:
        normalized package name
    """
    return PATTERN_DELIMITER.sub("-", pkg_name).lower().strip()


def normalize_version(version_string: Union[str, None]) -> str:
    """
    Normalize a version string to a PEP 440 compliant format.

    Args:
        version_string (str): The version string to normalize.

    Returns:
        str: A normalized version string in PEP 440 format or empty if invalid.
    """
    _regex = re.compile(
        rf"^\s*{VERSION_PATTERN}\s*$",
        re.VERBOSE | re.IGNORECASE,
    )
    match = _regex.match(version_string) if version_string else None
    if not match:
        return ""
    epoch = match.group("epoch") or "0"
    release = match.group("release") or "0.0"
    pre = (
        f"{match.group('pre_l')}{match.group('pre_n')}"
        if match.group("pre_n")
        else match.group("pre_l")
    )
    post = (
        f"{match.group('post_l')}{match.group('post_n2')}"
        if match.group("post_n2")
        else match.group("post_n1")
    )
    dev = (
        f"{match.group('dev_l')}{match.group('dev_n')}"
        if match.group("dev_n")
        else match.group("dev_l")
    )
    # Building the normalized version string
    normalized_version = f"{epoch}!{release}" if epoch != "0" else release
    if pre:
        normalized_version += f"{pre}"
    if post:
        normalized_version += f"{post}"
    if dev:
        normalized_version += f"{dev}"
    if match.group("local"):
        normalized_version += f"+{match.group('local')}"
    return normalized_version


def normalize_pkg_name_and_version(pkg_name_version: str) -> str:
    """Return normalized name according to PEP specification

    Args:
        pkg_name_version: Package name optionally include version

    Returns:
        normalized package name and version
    """
    pkg_name, sep, version = pkg_name_version.partition(":")
    return normalize_pkg_name(pkg_name) + sep + normalize_version(version)


def deduplicate_and_normalize(
    packages: Iterable[str],
) -> Generator[str, None, None]:
    """Normalize and deduplicate a list of package names.

    This generator function takes an iterable of package names,
    normalizes each package name, and yields only unique normalized
    names, preserving the order of their first occurrence.

    Args:
        packages (Iterable[str]): An iterable containing package names
                                  that need to be normalized. The input
                                  can be a list, tuple, or any other
                                  iterable of strings.

    Yields:
        str: A unique normalized package name each time this
             function is called. The normalization is performed
             by the `normalize_pkg_name` function.

    """
    seen: set[str] = set()
    for pkg in packages:
        norm_pkg: str = normalize_pkg_name(pkg)
        if norm_pkg not in seen:
            seen.add(norm_pkg)
            yield norm_pkg


# Mapping of FIELD_NAMES to METADATA_KEYS where they differ by more than case
FIELDS_TO_METADATA_KEYS: dict[str, str] = {
    "URL": "home-page",
    "Description": "summary",
    "License-Metadata": "license",
    "License-Classifier": "license_classifier",
    "License-Expression": "license_expression",
}

from .core import (
    get_packages,
    SYSTEM_PACKAGES,
)


def _handle_multiple_value_field(
    key: str, value: Iterator[str]
) -> str | list[str]:
    """Normalize a metadata field that may contain one or many values.

    This helper converts an iterator of field values into the most convenient
    representation based on the field name:

    - If the field name ends with ``"s"`` (case-insensitive), the values are
      treated as plural and returned as a list.
    - Otherwise, the first value is returned as a single string.
    - If a plural field has no values, ``["UNKNOWN"]`` is returned.
    - If a singular field has no values, ``LICENSE_UNKNOWN`` is returned.

    Args:
        key: The field name used to decide whether the field should be treated
            as singular or plural.
        value: An iterator of string values for the field.

    Returns:
        Either:
        - a list of strings for plural fields, or
        - a single string for singular fields.

    Examples:
        A plural field returns all values as a list:

        >>> _handle_multiple_value_field("authors", iter(["Alice", "Bob"]))
        ['Alice', 'Bob']

        A singular field returns the first value:

        >>> _handle_multiple_value_field("license", iter(["MIT", "BSD"]))
        'MIT'

        An empty plural field falls back to ``["UNKNOWN"]``:

        >>> _handle_multiple_value_field("authors", iter([]))
        ['UNKNOWN']

        An empty singular field falls back to ``LICENSE_UNKNOWN``:

        >>> _handle_multiple_value_field("license", iter([]))
        'UNKNOWN'
    """
    if key.lower().endswith("s"):
        return list(value) or ["UNKNOWN"]
    return cast(str, next(value, LICENSE_UNKNOWN))


def create_licenses_table(
    args: CustomNamespace,
    output_fields: set[str] | Sequence[str] = DEFAULT_OUTPUT_FIELDS,
) -> PrettyTable:
    table = factory_styled_table_with_args(args, output_fields)

    for pkg in get_packages(args):
        row: list[str | list[str]] = []
        for field in output_fields:
            if field == "License":
                license_set = select_license_by_source(
                    args.from_,
                    cast(list[str], pkg["license_classifier"]),
                    cast(str, pkg["license"]),
                    cast(str, pkg["license_expression"]),
                )
                _sorted_license_set = (
                    sorted(license_set) if license_set else []
                )
                _normalized_license_set = {
                    normal_item
                    for normal_item in _sorted_license_set
                    if normal_item is not None
                }
                license_str = "; ".join(_normalized_license_set)
                row.append(license_str)
            elif field == "License-Classifier":
                row.append(
                    "; ".join(sorted(pkg["license_classifier"]))
                    or LICENSE_UNKNOWN
                )
            elif field == "License-Expression":
                row.append(
                    cast(str, pkg["license_expression"]) or LICENSE_UNKNOWN
                )
            elif field == "License-Metadata":
                row.append(cast(str, pkg["license"]) or LICENSE_UNKNOWN)
            elif (field.lower() in pkg) or (hasattr(pkg, field.lower())):
                row.append(cast(str, pkg[field.lower()]))
            else:
                if (field in FIELDS_TO_METADATA_KEYS) and (
                    FIELDS_TO_METADATA_KEYS[field] in pkg
                ):
                    value = pkg[FIELDS_TO_METADATA_KEYS[field]]
                    if value:
                        if field in _MULTI_VALUE_KEYS:
                            row.append(
                                cast(
                                    list[str],
                                    _handle_multiple_value_field(
                                        key=field,
                                        value=cast(Iterator[str], [*value]),
                                    ),
                                )
                            )
                        else:
                            row.append(cast(str, value))
                    else:  # invalid value (e.g. None)
                        row.append(LICENSE_UNKNOWN)
                else:  # Unknown value (e.g. custom/future fields)
                    row.append(LICENSE_UNKNOWN)

        table.add_row(row)

    return table


def create_summary_table(args: CustomNamespace) -> PrettyTable:
    counts = Counter(
        "; ".join(
            sorted(
                select_license_by_source(
                    args.from_,
                    cast(list[str], pkg["license_classifier"]),
                    cast(str, pkg["license"]),
                    cast(str, pkg["license_expression"]),
                )
            )
        )
        for pkg in get_packages(args)
    )

    table = factory_styled_table_with_args(args, SUMMARY_FIELD_NAMES)
    for license, count in counts.items():
        table.add_row([count, license])
    return table


# may not need these in module scope
# TODO: remove these from module API (instead keep as only internal)
from .sorting import (
    case_insensitive_set_intersect,
    case_insensitive_partial_match_set_intersect,
    case_insensitive_partial_match_set_diff,
    case_insensitive_set_diff,
)


from .core import (
    find_license_from_classifier,
    select_license_by_source,
)


# this should go in sorting -- duplicate regression
def get_sortby(args: CustomNamespace) -> str:
    if args.summary and args.order == OrderArg.COUNT:
        return "Count"
    elif args.summary or args.order == OrderArg.LICENSE:
        return "License"
    elif args.order == OrderArg.NAME:
        return "Name"
    elif args.order == OrderArg.AUTHOR and args.with_authors:
        return "Author"
    elif args.order == OrderArg.MAINTAINER and args.with_maintainers:
        return "Maintainer"
    elif args.order == OrderArg.URL and args.with_urls:
        return "URL"

    return "Name"


def load_config_from_file(pyproject_path: str) -> dict:
    if Path(pyproject_path).exists():
        with _real_io_open(pyproject_path, "rb") as f:
            return tomllib.load(f).get("tool", {}).get(__pkgname__, {})
    return {}


open = _real_io_open  # noqa: PLW0127  # set to _real_io_open (before monkey patching)


from .output import (
    JsonPrettyTable,
    JsonLicenseFinderTable,
    CSVPrettyTable,
    PlainVerticalTable,
    get_output_fields,
    create_output_string,
    factory_styled_table_with_args,
    save_if_needs,
    output_colored,
)


def create_warn_string(args: CustomNamespace) -> str:
    warn_messages = []
    warn = partial(output_colored, "33")

    if args.with_license_file and args.format_ != FormatArg.JSON:
        message = warn(
            "Due to the length of these fields, this option is "
            "best paired with --format=json."
        )
        warn_messages.append(message)

    if args.summary and (args.with_authors or args.with_urls):
        message = warn(
            "When using this option, only --order=count or "
            "--order=license has an effect for the --order "
            "option. And using --with-authors and --with-urls "
            "will be ignored."
        )
        warn_messages.append(message)

    return "\n".join(warn_messages)


# placeholder for something like:
#import .cli as cli


from .__main__ import main
