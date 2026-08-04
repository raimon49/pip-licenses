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
from importlib import metadata as importlib_metadata
from importlib.metadata import Distribution
from pathlib import Path
from typing import TYPE_CHECKING, cast

from prettytable import HRuleStyle, PrettyTable, RowType

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-not-found]  # ty: ignore[unused-type-ignore-comment]

if TYPE_CHECKING:  # pragma: no cover
    from email.message import Message
    from importlib.metadata import PackagePath


open = open  # noqa: PLW0127  # allow monkey patching

__pkgname__ = "pip-licenses"
__version__ = "6.0.0b0"  # (dev-v6.0 branch)
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


def extract_urls(metadata: Message) -> dict[str, str | list[str] | None]:
    """Extract normalized project URLs from message metadata.

    This scans all ``Project-URL`` entries in the given metadata object and
    builds a dictionary keyed by the lowercased, stripped, label value of
    the pair (e.g., 'source' for 'Source, https://github.com/user/repo.git').

    Each ``Project-URL`` entry is expected to contain exactly one comma
    separating the label and URL, for example::

        Project-URL: Homepage, https://github.com/raimon49/pip-licenses

    Duplicate labels are merged into a list on the second occurrence of a key.
    The first value remains a string until a duplicate is encountered.
    Empty URL values are normalized to ``None``. For canonical Specification:
    [Core Metadata 1.2 (PEP 753)](https://packaging.python.org/en/latest/specifications/core-metadata/#core-metadata-project-url).

    Args:
        metadata: A message-like object supporting ``get_all("Project-URL", [])``
            and returning a sequence of comma-separated ``"name, url"`` strings.

    Returns:
        A mapping from normalized project names to:
        - a stripped URL string,
        - a list of URL strings if the same project name appears multiple times,
        - or ``None`` if the URL portion is empty.

    Raises:
        ValueError: If a ``Project-URL`` entry does not contain a comma.

    Examples:
        Basic extraction:

        >>> class DummyMessage:
        ...     def __init__(self, values):
        ...         self._values = values
        ...     def get_all(self, key, default=None):
        ...         return self._values if key == "Project-URL" else default
        ...
        >>> metadata = DummyMessage([
        ...     "Homepage, https://github.com/raimon49/pip-licenses",
        ...     "Bug Tracker, https://github.com/raimon49/pip-licenses/issues",
        ... ])
        >>> extract_urls(metadata)
        {'homepage': 'https://github.com/raimon49/pip-licenses', 'bug tracker': 'https://github.com/raimon49/pip-licenses/issues'}

        Duplicate labels are collected into a list:

        >>> metadata = DummyMessage([
        ...     "Homepage, https://github.com/raimon49/pip-licenses",
        ...     "Homepage, https://pypi.org/project/pip-licenses",
        ... ])
        >>> extract_urls(metadata)
        {'homepage': ['https://github.com/raimon49/pip-licenses', 'https://pypi.org/project/pip-licenses']}

        Empty URLs become ``None``:

        >>> metadata = DummyMessage([
        ...     "Source,   ",
        ... ])
        >>> extract_urls(metadata)
        {'source': None}
    """
    _urls: dict[str, str | list[str] | None] = {}
    for entry in metadata.get_all("Project-URL", []):
        key, value = entry.split(",", 1)
        _norm_key: str = key.strip().lower()
        _norm_val = value.strip()
        if _norm_key in _urls:
            if not isinstance(_urls[_norm_key], list):
                # MyPy is a bit lost by this point, (See Discussion in PR #346)
                # https://github.com/raimon49/pip-licenses/pull/346#discussion_r3661511932
                _urls[_norm_key] = [
                    _urls[_norm_key],  # type: ignore[list-item]  # ty: ignore[unused-type-ignore-comment]
                ]
            if _norm_val not in set(
                cast(list[str], _urls[_norm_key]),
            ):  # deduplicate and merge by key
                _urls[_norm_key].append(_norm_val)  # type: ignore[union-attr]  # ty: ignore[unused-type-ignore-comment]
        else:
            _urls[_norm_key] = _norm_val or None
    return _urls


def extract_homepage(metadata: Message) -> str | None:
    """Extracts a homepage attribute from the package metadata.

    Retrieve home page from the PEP 753 `Project-URL` metadata.
    As a fallback, try the Core Metadata 1.0 home-page attribute.
    If all else fails, try other PEP 753 `Project-URL` labels.

    Args:
        metadata: The package metadata to extract the home page from.

    Returns:
        The home page if applicable, None otherwise.

    Raises:
        ValueError: Raised when called with incompatible package
                    metadata. May indicate a
                    CWE-20 in caller. Mitigates theoretical CWE-1287
                    by raising.
    """
    # Morally, this should be typed as a dict[str, str | list[str]] (but we'll handle None too)
    candidates: dict[str, str | list[str] | None] = extract_urls(metadata)

    def _help_get_first_of_many(
        raw_input: str | list[str] | None,
    ) -> str | None:
        """Selects a up to a single string from the given input.

        Utility; Not part of exposed API. Helps by handling the
        zero-one-infinity principle.

        Pseudo-logic:
          A. Unless the input is non-None, just return None.
          B. If input is a string, then just return the input string.
          C. Otherwise if input is a list and has at least one value,
             then return the first value as a string.
          D. Otherwise raise a ValueError (likely a regression)

        Args:
            raw_input: One or more strings. (optional)

        Returns:
            The first input string (if applicable), None otherwise.

        Raises:
            ValueError: Raised when called with incompatible package
                        metadata. May indicate a CWE-20 in caller.
                        Mitigates theoretical CWE-1287 by raising.
        """
        if raw_input is not None:
            if isinstance(raw_input, str):
                return raw_input
            elif raw_input[0]:
                return cast(
                    str, raw_input[0]
                )  # overkill explicit cast (for linters)
            else:  # pragma: no cover
                raise ValueError(
                    "BUG-242: If you encounter this error, please file a regression bug."
                    "You have found a regression bug caused by changes introduced by "
                    "[GHI #242](https://github.com/raimon49/pip-licenses/issues/242)"
                ) from None
        return None

    # start with Core Metadata 1.2 (PEP 753)
    # https://packaging.python.org/en/latest/specifications/core-metadata/#core-metadata-project-url
    homepage = candidates.get("homepage")
    if homepage is not None:
        return _help_get_first_of_many(homepage)

    # fall back to deprecated Core Metadata 1.0
    # https://packaging.python.org/en/latest/specifications/core-metadata/#home-page
    homepage = metadata.get("home-page", None)
    if homepage is not None:
        return _help_get_first_of_many(homepage)

    _has_something_flag = False
    # if all else fails, try alternative Core Metadata 1.2 labels
    # https://packaging.python.org/en/latest/specifications/well-known-project-urls/#well-known-labels
    for priority_key in (
        "source",
        "repository",
        "changelog",
        "documentation",
        "bug tracker",
    ):
        if priority_key in candidates:
            _has_something_flag = True
            _val = _help_get_first_of_many(candidates[priority_key])
            if _val:
                return _val
    if _has_something_flag:
        return LICENSE_UNKNOWN
    return None


def extract_license_from_classifiers(metadata: Message) -> list[str]:
    classifiers: list[str] = metadata.get_all("classifier", [])
    license_classifiers: list[str] = find_license_from_classifier(classifiers)
    return license_classifiers


PATTERN_DELIMITER: re.Pattern = re.compile(r"[-_.]+")


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


def normalize_version(version_string: str | None) -> str:
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


METADATA_KEYS: dict[
    str,
    list[
        Callable[
            [Message],
            str | list[str] | dict[str, str | list[str] | None] | None,
        ]
    ],
] = {
    "home-page": [extract_homepage],
    "author": [
        lambda metadata: metadata.get("author"),
        lambda metadata: metadata.get("author-email"),
    ],
    "maintainer": [
        lambda metadata: metadata.get("maintainer"),
        lambda metadata: metadata.get("maintainer-email"),
    ],
    "license": [lambda metadata: metadata.get("license")],
    "license_classifier": [extract_license_from_classifiers],
    "license_expression": [
        lambda metadata: metadata.get("license-expression")
    ],
    "license_files": [lambda metadata: metadata.get_all("License-File", [])],
    "summary": [lambda metadata: metadata.get("summary")],
    "urls": [extract_urls],
}

# Mapping of FIELD_NAMES to METADATA_KEYS where they differ by more than case
FIELDS_TO_METADATA_KEYS: dict[str, str] = {
    "URL": "home-page",
    "Description": "summary",
    "License-Metadata": "license",
    "License-Classifier": "license_classifier",
    "License-Expression": "license_expression",
    "LicenseFile": "license_files",
    "LicenseFiles": "license_files",
    "LicenseText": "license_texts",
    "LicenseTexts": "license_texts",
    "NoticeFile": "notice_files",
    "NoticeFiles": "notice_files",
    "NoticeText": "notice_texts",
    "NoticeTexts": "notice_texts",
    "OtherFiles": "other_files",
    "OtherTexts": "other_texts",
}

_MULTI_VALUE_KEYS: set[str] = {
    "LicenseFile",
    "LicenseFiles",
    "LicenseText",
    "LicenseTexts",
    "NoticeFile",
    "NoticeFiles",
    "NoticeText",
    "NoticeTexts",
    "OtherFiles",
    "OtherTexts",
}

SYSTEM_PACKAGES: list[str] = [
    __pkgname__,
    "pip",
    "prettytable",
    "wcwidth",
    "setuptools",
    "wheel",
]
if sys.version_info < (3, 11):
    SYSTEM_PACKAGES.append("tomli")

LICENSE_UNKNOWN: str = "UNKNOWN"


def get_packages(
    args: CustomNamespace,
) -> Iterator[dict[str, str | list[str] | dict[str, str | list[str] | None]]]:
    def filter_pkg_included_paths(
        pkg: Distribution, file_names_rgx: str
    ) -> set[PackagePath]:
        """
        Attempt to find the set of package's matching files included on-disk.
        """
        pkg_files = pkg.files or ()
        pattern: re.Pattern = re.compile(file_names_rgx)
        matched_rel_paths = {
            file for file in pkg_files if pattern.match(file.name)
        }
        return matched_rel_paths

    def filter_pkg_included_files(
        pkg: Distribution, file_names_rgx: str
    ) -> set[str]:
        """
        Attempt to find the set of package's matching files included on-disk.

        Matching pathstrings are returned as relative paths to the package on-disk.
        """
        matched_rel_paths = filter_pkg_included_paths(pkg, file_names_rgx)
        included_files_set: set[str] = set()
        for rel_path in matched_rel_paths:
            abs_path = Path(str(pkg.locate_file(rel_path)))
            if not abs_path.is_file():
                continue  # pragma: no cover
            included_file = str(rel_path)
            included_files_set.add(included_file)

        return included_files_set

    def get_pkg_included_file(
        pkg: Distribution, file_names_rgx: str
    ) -> tuple[str | None, str | None]:
        """
        Attempt to find the package's included file on disk and return the
        tuple (included_file_path, included_file_contents).
        """
        included_file = None
        included_text = LICENSE_UNKNOWN
        matched_rel_paths = filter_pkg_included_paths(pkg, file_names_rgx)

        for rel_path in matched_rel_paths:
            abs_path = Path(str(pkg.locate_file(rel_path)))
            if not abs_path.is_file():
                continue  # pragma: no cover
            included_file = str(abs_path)
            with open(
                abs_path, encoding="utf-8", errors="backslashreplace"
            ) as included_file_handle:
                included_text = included_file_handle.read()
            break
        return (included_file, included_text)

    def get_pkg_license_texts_from_disk(
        pkg: Distribution, filelist: list[str] | None = None
    ) -> list[str | None] | None:
        if filelist:
            license_texts = []
            for a_license_file in filelist:
                if a_license_file:
                    _fh, a_license_file_text = get_pkg_included_file(
                        pkg, a_license_file
                    )
                    if _fh:
                        license_texts.append(a_license_file_text)
            return license_texts
        return None

    def fallback_license_retrieval(
        pkg: Distribution,
    ) -> dict[str, str]:
        """
        Fallback logic for retrieving licenses and other metadata files.

        See also https://github.com/raimon49/pip-licenses/issues/309

        Parameters:
        - pkg: The package object or identifier.

        Returns:
        - A dictionary containing license details and other metadata.
        """
        license_file_pattern = (
            r"[Ll][Ii][Cc][Ee][Nn][Cc][Ee].*|[Cc][Oo][Pp][Yy][Ii][Nn][Gg].*"
        )
        notice_file_pattern = r"NOTICE.*"
        author_file_pattern = r"[Aa][Uu][Tt][Hh][Oo][Rr][Ss].*"

        license_file, license_text = get_pkg_included_file(
            pkg, license_file_pattern
        )
        notice_file, notice_text = get_pkg_included_file(
            pkg, notice_file_pattern
        )
        author_file, author_text = get_pkg_included_file(
            pkg, author_file_pattern
        )
        FILE_MISSING = ""
        return {
            "license_file": license_file or LICENSE_UNKNOWN,
            "license_text": license_text or LICENSE_UNKNOWN,
            "notice_file": notice_file or FILE_MISSING,
            "notice_text": notice_text or FILE_MISSING,
            "author_file": author_file or FILE_MISSING,
            "author_text": author_text or FILE_MISSING,
        }

    def get_pkg_info(
        pkg: Distribution,
    ) -> dict[str, str | list[str] | dict[str, str | list[str] | None]]:
        pkg_name: str = pkg.metadata["name"]
        normal_pkg_name = normalize_pkg_name(pkg_name)
        legacy_info = fallback_license_retrieval(pkg)
        pkg_info: dict[
            str, str | list[str] | dict[str, (str | list[str] | None)]
        ] = {
            "name": pkg_name,
            "version": pkg.version,
            "namever": f"{normal_pkg_name} {pkg.version}",
            "licensefile": legacy_info["license_file"],  # DEPRECIATED in v6.0+
            "licensetext": legacy_info["license_text"],  # DEPRECIATED in v6.0+
            "noticefile": legacy_info["notice_file"],  # DEPRECIATED in v6.0+
            "noticetext": legacy_info["notice_text"],  # DEPRECIATED in v6.0+
            "otherfile": legacy_info["author_file"],  # DEPRECIATED in v6.0+
            "othertext": legacy_info["author_text"],  # DEPRECIATED in v6.0+
        }
        # filter the legacy info and union
        pkg_info |= {
            leg_key: leg_value
            for leg_key, leg_value in legacy_info.items()
            if (
                leg_value
                and (leg_value is not None)
                and (len(leg_value) > 0)
                and (leg_value is not LICENSE_UNKNOWN)
            )
        }

        metadata = pkg.metadata
        for field_name, field_selector_fns in METADATA_KEYS.items():
            value = None
            for field_selector_fn in field_selector_fns:
                # Type hint of `Distribution.metadata` states `PackageMetadata`
                # but it's actually of type `email.message.Message`
                value = field_selector_fn(metadata)  # type: ignore[arg-type]
                if value:
                    break
            pkg_info[field_name] = value  # type: ignore[assignment]

        if args.with_license_files:  # conditional for < v6+
            pkg_texts: list[str | None] | None = (
                get_pkg_license_texts_from_disk(
                    pkg,
                    filelist=cast(list[str], pkg_info["license_files"])
                    if pkg_info["license_files"]
                    else None,
                )
            )
            if (
                pkg_texts and None not in pkg_texts
            ):  # https://github.com/raimon49/pip-licenses/pull/346#discussion_r3609573407
                pkg_info["license_texts"] = cast(list[str], pkg_texts)

        if args.with_other_files:  # conditional for < v6+
            # TODO: [GHI-394](https://github.com/raimon49/pip-licenses/issues/349)
            OTHER_FILES_PATTERN = r"[Aa][Uu][Tt][Hh][Oo][Rr][Ss].*|[Cc][Oo][Pp][Yy][Ii][Nn][Gg].*|[Ll][Ee][Gg][Aa][Ll].*"
            pkg_info["other_files"] = list(
                filter_pkg_included_files(pkg, OTHER_FILES_PATTERN),
            )
            pkg_other_texts: list[str | None] | None = (
                get_pkg_license_texts_from_disk(
                    pkg,
                    filelist=cast(list[str], pkg_info["other_files"])
                    if pkg_info["other_files"]
                    else None,
                )
            )
            if pkg_other_texts is not None:
                pkg_info["other_texts"] = cast(list[str], pkg_other_texts)

        if args.filter_strings:

            def filter_string(item: str) -> str:
                try:
                    return item.encode(
                        args.filter_code_page, errors="ignore"
                    ).decode(args.filter_code_page)
                except AttributeError as _cause:  # pragma: no cover
                    _context_details = f"{item} can not be safely filtered with {args.filter_code_page}"
                    if not isinstance(item, str):
                        _context_details = (
                            f"{type(item)} can not be filtered as a string"
                        )
                    raise ValueError(_context_details) from _cause

            def do_filter_iteration(
                sub_item: str | list[str] | dict[str, str | list[str] | None],
            ) -> str | list[str] | dict[str, str | list[str] | None]:
                if isinstance(sub_item, list):
                    return list(map(filter_string, sub_item))
                elif isinstance(sub_item, dict):
                    _filtered_subset: dict[str, str | list[str] | None] = (
                        sub_item.copy()
                    )
                    for k, v in sub_item.items():
                        if v is not None:  # Prune None values
                            _filtered_subset[k] = do_filter_iteration(v)  # type: ignore[assignment]
                    return _filtered_subset
                else:
                    return filter_string(cast(str, sub_item))

            for key, val in pkg_info.items():
                if val is not None:  # ignore top-level None values
                    pkg_info[key] = do_filter_iteration(val)

        return pkg_info

    def get_python_sys_path(executable: str) -> list[str]:
        script = "import sys; print(' '.join(filter(bool, sys.path)))"
        output = subprocess.run(
            [executable, "-c", script],
            capture_output=True,
            env={**os.environ, "PYTHONPATH": "", "VIRTUAL_ENV": ""},
            check=False,
        )
        return output.stdout.decode().strip().split()

    if args.python == sys.executable:
        search_paths = sys.path
    else:
        search_paths = get_python_sys_path(args.python)

    pkgs = importlib_metadata.distributions(path=search_paths)
    ignore_pkgs_as_normalize = [
        normalize_pkg_name_and_version(pkg) for pkg in args.ignore_packages
    ]
    pkgs_as_normalize = list(deduplicate_and_normalize(args.packages))

    fail_on_licenses = set()
    if args.fail_on:
        # filter None types out
        fail_on_licenses = set(
            filter(None, map(str.strip, args.fail_on.split(";")))
        )

    allow_only_licenses = set()
    if args.allow_only:
        # filter None types out
        allow_only_licenses = set(
            filter(None, map(str.strip, args.allow_only.split(";")))
        )

    for pkg in pkgs:
        pkg_name = normalize_pkg_name(pkg.metadata["name"])
        pkg_version = pkg.metadata["version"]
        pkg_name_and_version = f"{pkg_name}:{pkg_version}"

        if (
            pkg_name.lower() in ignore_pkgs_as_normalize
            or pkg_name_and_version.lower() in ignore_pkgs_as_normalize
        ):
            continue

        if pkgs_as_normalize and pkg_name.lower() not in pkgs_as_normalize:
            continue

        if not args.with_system and pkg_name in SYSTEM_PACKAGES:
            continue

        pkg_info = get_pkg_info(pkg)

        license_names = select_license_by_source(
            args.from_,
            cast(list[str], pkg_info["license_classifier"]),
            cast(str, pkg_info["license"]),
            cast(str, pkg_info["license_expression"]),
        )

        if fail_on_licenses:
            failed_licenses = set()
            if not args.partial_match:
                failed_licenses = case_insensitive_set_intersect(
                    license_names, fail_on_licenses
                )
            else:
                failed_licenses = case_insensitive_partial_match_set_intersect(
                    license_names, fail_on_licenses
                )
            if failed_licenses:
                sys.stderr.write(
                    "fail-on license {} was found for package {}:{}\n".format(
                        "; ".join(sorted(failed_licenses)),
                        pkg_info["name"],
                        pkg_info["version"],
                    )
                )
                sys.exit(1)

        if allow_only_licenses:
            uncommon_licenses = set()
            if not args.partial_match:
                uncommon_licenses = case_insensitive_set_diff(
                    license_names, allow_only_licenses
                )
            else:
                uncommon_licenses = set(
                    case_insensitive_partial_match_set_diff(
                        license_names, allow_only_licenses
                    )
                )

            if len(uncommon_licenses) == len(license_names):
                sys.stderr.write(
                    "license {} not in allow-only licenses was found"
                    " for package {}:{}\n".format(
                        "; ".join(sorted(uncommon_licenses)),
                        pkg_info["name"],
                        pkg_info["version"],
                    )
                )
                sys.exit(1)

        yield pkg_info


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


def case_insensitive_set_intersect(
    set_a: set[str] | list[str] | tuple | frozenset,
    set_b: set[str] | list[str] | tuple | frozenset,
) -> set:
    """Same as set.intersection() but case-insensitive"""
    common_items = set()
    set_b_lower = {item.lower() for item in set_b}
    for elem in set_a:
        if elem.lower() in set_b_lower:
            common_items.add(elem)
    return common_items


def case_insensitive_partial_match_set_intersect(
    set_a: set[str] | list[str] | tuple | frozenset,
    set_b: set[str] | list[str] | tuple | frozenset,
) -> set:
    common_items = set()
    for item_a in set_a:
        for item_b in set_b:
            if item_b.lower() in item_a.lower():
                common_items.add(item_a)
    return common_items


def case_insensitive_partial_match_set_diff(
    set_a: set,
    set_b: set[str],
) -> set[str]:
    """
    Return items from set_a without case-insensitive partial matches
    from items in set_b.
    """
    uncommon_items = set_a.copy()
    for item_a in set_a:
        item_a_lower = item_a.lower()  # change case once & use for sub loop
        for item_b in set_b:
            if item_b.lower() in item_a_lower:
                uncommon_items.discard(item_a)
                break
    return uncommon_items


def case_insensitive_set_diff(
    set_a: set | list | tuple | frozenset,
    set_b: set[str] | list[str] | tuple | frozenset,
) -> set:
    """Same as set.difference() but case-insensitive"""
    uncommon_items = set()
    set_b_lower = {item.lower() for item in set_b}
    for elem in set_a:
        if elem.lower() not in set_b_lower:
            uncommon_items.add(elem)
    return uncommon_items


class JsonPrettyTable(PrettyTable):
    """PrettyTable-like class exporting to JSON"""

    def format_row(self, row: RowType) -> dict[str, str | list[str]]:
        return dict(zip(self._field_names, row))

    def get_string(self, **kwargs: str | list[str]) -> str:
        # import included here in order to limit dependencies
        # if not interested in JSON output,
        # then the dependency is not required
        import json

        options = self._get_options(kwargs)
        rows = self._get_rows(options)
        lines = [self.format_row(row) for row in rows]
        return json.dumps(lines, indent=2, sort_keys=True)


class JsonLicenseFinderTable(JsonPrettyTable):
    def format_row(self, row: RowType) -> dict[str, str | list[str]]:
        resrow: dict[str, str | list[str]] = {}
        for field, value in zip(self._field_names, row):
            if field == "Name":
                resrow["name"] = value

            if field == "Version":
                resrow["version"] = value

            if field == "License":
                resrow["licenses"] = [value]

        return resrow

    def get_string(self, **kwargs: str | list[str]) -> str:
        # import included here in order to limit dependencies
        # if not interested in JSON output,
        # then the dependency is not required
        import json

        options = self._get_options(kwargs)
        rows = self._get_rows(options)
        lines = [self.format_row(row) for row in rows]
        return json.dumps(lines, sort_keys=True)


class CSVPrettyTable(PrettyTable):
    """PrettyTable-like class exporting to CSV"""

    def get_string(self, **kwargs: str | list[str]) -> str:
        def esc_quotes(val: bytes | str) -> str:
            """
            Meta-escaping double quotes
            https://tools.ietf.org/html/rfc4180
            """
            try:
                return cast(str, val).replace('"', '""')
            except UnicodeDecodeError:  # pragma: no cover
                return cast(bytes, val).decode("utf-8").replace('"', '""')
            except UnicodeEncodeError:  # pragma: no cover
                return str(
                    cast(str, val).encode("unicode_escape").replace('"', '""')  # type: ignore[arg-type]
                )

        options = self._get_options(kwargs)
        rows = self._get_rows(options)
        formatted_rows = self._format_rows(rows)

        lines: list[str] = []
        formatted_header = ",".join(
            [f'"{esc_quotes(val)}"' for val in self._field_names]
        )
        lines.append(formatted_header)
        lines.extend(
            [
                ",".join([f'"{esc_quotes(val)}"' for val in row])
                for row in formatted_rows
            ]
        )

        return "\n".join(lines)


class PlainVerticalTable(PrettyTable):
    """PrettyTable for outputting to a simple non-column based style.

    When used with --with-license-file, this style is similar to the default
    style generated from Angular CLI's --extractLicenses flag.
    """

    def get_string(self, **kwargs: str | list[str]) -> str:
        options = self._get_options(kwargs)
        rows = self._get_rows(options)
        show_paths = "LicenseFiles" in kwargs["fields"]

        output = ""
        for row in rows:
            index = 0
            while index < len(row):
                v = row[index]
                if isinstance(v, list):
                    if show_paths:
                        for first_entry, second_entry in zip(
                            v, row[index + 1]
                        ):
                            output += f"{first_entry}\n{second_entry}\n"
                        index += 1
                    else:  # pragma: no cover
                        for entry in v:
                            output += f"{entry}\n"
                else:
                    output += f"{v}\n"
                index += 1
            output += "\n"

        return output


def factory_styled_table_with_args(
    args: CustomNamespace,
    output_fields: set[str] | Sequence[str] = DEFAULT_OUTPUT_FIELDS,
) -> PrettyTable:
    table = PrettyTable()
    table.field_names = output_fields  # type: ignore[assignment]
    table.align = "l"  # type: ignore[assignment]
    table.border = args.format_ in (
        FormatArg.MARKDOWN,
        FormatArg.RST,
        FormatArg.CONFLUENCE,
        FormatArg.JSON,
    )
    table.header = True

    if args.format_ == FormatArg.MARKDOWN:
        table.junction_char = "|"
        table.hrules = HRuleStyle.HEADER
    elif args.format_ == FormatArg.RST:
        table.junction_char = "+"
        table.hrules = HRuleStyle.ALL
    elif args.format_ == FormatArg.CONFLUENCE:
        table.junction_char = "|"
        table.hrules = HRuleStyle.NONE
    elif args.format_ == FormatArg.JSON:
        table = JsonPrettyTable(table.field_names)
    elif args.format_ == FormatArg.JSON_LICENSE_FINDER:
        table = JsonLicenseFinderTable(table.field_names)
    elif args.format_ == FormatArg.CSV:
        table = CSVPrettyTable(table.field_names)
    elif args.format_ == FormatArg.PLAIN_VERTICAL:
        table = PlainVerticalTable(table.field_names)

    return table


def find_license_from_classifier(classifiers: list[str]) -> list[str]:
    licenses = []
    for classifier in filter(lambda c: c.startswith("License"), classifiers):
        license = classifier.split(" :: ")[-1]

        # Through the declaration of 'Classifier: License :: OSI Approved'
        if license != "OSI Approved":
            licenses.append(license)

    return licenses


def select_license_by_source(
    from_source: FromArg,
    license_classifier: list[str],
    license_meta: str,
    license_expression: str,
) -> set[str]:
    if license_expression and license_expression != LICENSE_UNKNOWN:
        return {license_expression}

    license_classifier_set = (
        set(license_classifier) if license_classifier else {LICENSE_UNKNOWN}
    )
    if (
        from_source == FromArg.CLASSIFIER
        or from_source == FromArg.MIXED
        and len(license_classifier) > 0
    ):
        return license_classifier_set
    else:
        return {license_meta}


def get_output_fields(args: CustomNamespace) -> list[str]:
    if args.summary:
        return list(SUMMARY_OUTPUT_FIELDS)

    output_fields = list(DEFAULT_OUTPUT_FIELDS)

    if args.from_ == FromArg.ALL:
        output_fields.append("License-Metadata")
        output_fields.append("License-Classifier")
        output_fields.append("License-Expression")
    else:
        output_fields.append("License")

    if args.with_authors:
        output_fields.append("Author")

    if args.with_maintainers:
        output_fields.append("Maintainer")

    if args.with_urls:
        output_fields.append("URL")

    if args.with_description:
        output_fields.append("Description")

    if args.no_version:
        output_fields.remove("Version")

    if args.with_license_files and args.format_ not in [
        FormatArg.JSON,
        FormatArg.PLAIN_VERTICAL,
    ]:
        if args.format_ != FormatArg.HTML:
            args.with_license_files = False  # unsupported combo
        args.with_notice_file = False
        args.with_notice_files = False
        args.with_other_files = False

    if args.no_file_paths:
        args.no_license_path = True

    if args.with_license_file or args.with_license_files:
        if not args.no_license_path:
            output_fields.append(
                "LicenseFiles" if args.with_license_files else "LicenseFile"
            )

        output_fields.append(
            "LicenseTexts" if args.with_license_files else "LicenseText"
        )

        if args.with_notice_file or args.with_notice_files:
            if not args.no_file_paths:
                output_fields.append(
                    "NoticeFiles" if args.with_notice_files else "NoticeFile"
                )
            output_fields.append("NoticeText")

        if args.with_other_files:
            if not args.no_file_paths:
                output_fields.append("OtherFiles")
            output_fields.append("OtherText")

    return output_fields


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


def create_output_string(args: CustomNamespace) -> str:
    output_fields = get_output_fields(args)

    if args.summary:
        table = create_summary_table(args)
    else:
        table = create_licenses_table(args, output_fields)

    sortby = get_sortby(args)

    if args.format_ == FormatArg.HTML:
        html = table.get_html_string(fields=output_fields, sortby=sortby)
        return html.encode("ascii", errors="xmlcharrefreplace").decode("ascii")
    else:
        return table.get_string(fields=output_fields, sortby=sortby)


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


class CustomHelpFormatter(argparse.HelpFormatter):  # pragma: no cover
    def __init__(
        self,
        prog: str,
        indent_increment: int = 2,
        max_help_position: int = 24,
        width: int | None = None,
    ) -> None:
        max_help_position = 30
        super().__init__(
            prog,
            indent_increment=indent_increment,
            max_help_position=max_help_position,
            width=width,
        )

    def _format_action(self, action: argparse.Action) -> str:
        flag_indent_argument: bool = False
        text = self._expand_help(action)
        separator_pos = text[:3].find("|")
        if separator_pos != -1 and "I" in text[:separator_pos]:
            self._indent()
            flag_indent_argument = True
        help_str = super()._format_action(action)
        if flag_indent_argument:
            self._dedent()
        return help_str

    def _expand_help(self, action: argparse.Action) -> str:
        if isinstance(action.default, Enum):
            default_value = enum_key_to_value(action.default)
            return cast(str, self._get_help_string(action)) % {
                "default": default_value
            }
        return super()._expand_help(action)

    def _split_lines(self, text: str, width: int) -> list[str]:
        separator_pos = text[:3].find("|")
        if separator_pos != -1:
            flag_splitlines: bool = "R" in text[:separator_pos]
            text = text[separator_pos + 1:]  # fmt: skip
            if flag_splitlines:
                return text.splitlines()
        return super()._split_lines(text, width)


class CustomNamespace(argparse.Namespace):
    from_: FromArg
    order: OrderArg
    format_: FormatArg
    summary: bool
    output_file: str
    ignore_packages: list[str]
    packages: list[str]
    with_system: bool
    with_authors: bool
    with_urls: bool
    with_description: bool
    with_license_file: bool
    with_license_files: bool  # added in v6.0
    no_license_path: bool
    with_notice_file: bool
    with_notice_files: bool  # added in v6.0
    with_other_files: bool  # added in v6.0
    filter_strings: bool
    filter_code_page: str
    partial_match: bool
    fail_on: str | None
    allow_only: str | None


class CompatibleArgumentParser(argparse.ArgumentParser):
    def parse_args(  # type: ignore[override]
        self,
        args: Sequence[str] | None = None,
        namespace: CustomNamespace | None = None,
    ) -> CustomNamespace:
        args_ = cast(CustomNamespace, super().parse_args(args, namespace))
        self._verify_args(args_)
        return args_

    def _verify_args(self, args: CustomNamespace) -> None:
        if (
            args.with_license_file is False
            and args.with_license_files is False
        ) and (
            args.no_license_path is True
            or (
                (
                    args.with_notice_file is True
                    or args.with_notice_files is True
                )
                or args.with_other_files is True
            )
        ):
            self.error(
                "'--no-license-path' and '--with-notice-file[s]' "
                "as well as '--with-other-files' require "
                "the '--with-license-file[s]' option to be set"
            )
        if args.filter_strings is False and args.filter_code_page != "latin1":
            self.error(
                "'--filter-code-page' requires the '--filter-strings' "
                "option to be set"
            )
        try:
            codecs.lookup(args.filter_code_page)
        except LookupError:
            self.error(
                f"invalid code page '{args.filter_code_page}' given "
                "for '--filter-code-page, check "
                "https://docs.python.org/3/library/codecs.html#standard-encodings "
                "for valid code pages"
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


MAP_DEST_TO_ENUM: dict[str, type[NoValueEnum]] = {
    "from_": FromArg,
    "order": OrderArg,
    "format_": FormatArg,
}


class SelectAction(argparse.Action):
    def __call__(  # type: ignore[override]
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str,
        option_string: str | None = None,
    ) -> None:
        enum_cls = MAP_DEST_TO_ENUM[self.dest]
        setattr(namespace, self.dest, get_value_from_enum(enum_cls, values))


def load_config_from_file(pyproject_path: str) -> dict:
    if Path(pyproject_path).exists():
        with open(pyproject_path, "rb") as f:
            return tomllib.load(f).get("tool", {}).get(__pkgname__, {})
    return {}


def create_parser(
    pyproject_path: str = "pyproject.toml",
) -> CompatibleArgumentParser:
    parser = CompatibleArgumentParser(
        description=__summary__, formatter_class=CustomHelpFormatter
    )

    config_from_file = load_config_from_file(pyproject_path)

    common_options = parser.add_argument_group("Common options")
    license_file_options = parser.add_argument_group("License file options")
    format_options = parser.add_argument_group("Format options")
    verify_options = parser.add_argument_group("Verify options")

    lit_prog_pat = "%(prog)s"
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{lit_prog_pat} {__version__}",
    )

    common_options.add_argument(
        "--python",
        type=str,
        default=config_from_file.get("python", sys.executable),
        metavar="PYTHON_EXEC",
        help="R| path to python executable to search distributions from\n"
        "Package will be searched in the selected python's sys.path\n"
        "By default, will search packages for current env executable\n"
        "(default: sys.executable)",
    )

    common_options.add_argument(
        "--from",
        dest="from_",
        action=SelectAction,
        type=str,
        default=get_value_from_enum(
            FromArg, config_from_file.get("from", "mixed")
        ),
        metavar="SOURCE",
        choices=choices_from_enum(FromArg),
        help="R|where to find license information\n"
        '"meta", "classifier, "mixed", "all"\n'
        "(default: %(default)s)",
    )
    common_options.add_argument(
        "-o",
        "--order",
        action=SelectAction,
        type=str,
        default=get_value_from_enum(
            OrderArg, config_from_file.get("order", "name")
        ),
        metavar="COL",
        choices=choices_from_enum(OrderArg),
        help="R|order by column\n"
        '"name", "license", "author", "url"\n'
        "(default: %(default)s)",
    )
    common_options.add_argument(
        "-f",
        "--format",
        dest="format_",
        action=SelectAction,
        type=str,
        default=get_value_from_enum(
            FormatArg, config_from_file.get("format", "plain")
        ),
        metavar="STYLE",
        choices=choices_from_enum(FormatArg),
        help="R|dump as set format style\n"
        '"plain", "plain-vertical" "markdown", "rst", \n'
        '"confluence", "html", "json", \n'
        '"json-license-finder",  "csv"\n'
        "(default: %(default)s)",
    )
    common_options.add_argument(
        "--summary",
        action="store_true",
        default=config_from_file.get("summary", False),
        help="dump summary of each license",
    )
    common_options.add_argument(
        "--output-file",
        action="store",
        default=config_from_file.get("output-file"),
        type=str,
        help="save license list to file",
    )
    common_options.add_argument(
        "-i",
        "--ignore-packages",
        action="store",
        type=str,
        nargs="+",
        metavar="PKG",
        default=config_from_file.get("ignore-packages", []),
        help="ignore package name in dumped list",
    )
    common_options.add_argument(
        "-p",
        "--packages",
        action="store",
        type=str,
        nargs="+",
        metavar="PKG",
        default=config_from_file.get("packages", []),
        help="only include selected packages in output",
    )
    format_options.add_argument(
        "-s",
        "--with-system",
        action="store_true",
        default=config_from_file.get("with-system", False),
        help="dump with system packages",
    )
    format_options.add_argument(
        "-a",
        "--with-authors",
        action="store_true",
        default=config_from_file.get("with-authors", False),
        help="dump with package authors",
    )
    format_options.add_argument(
        "--with-maintainers",
        action="store_true",
        default=config_from_file.get("with-maintainers", False),
        help="dump with package maintainers",
    )
    format_options.add_argument(
        "-u",
        "--with-urls",
        action="store_true",
        default=config_from_file.get("with-urls", False),
        help="dump with package urls",
    )
    format_options.add_argument(
        "-d",
        "--with-description",
        action="store_true",
        default=config_from_file.get("with-description", False),
        help="dump with short package description",
    )
    format_options.add_argument(
        "-nv",
        "--no-version",
        action="store_true",
        default=config_from_file.get("no-version", False),
        help="dump without package version",
    )

    license_file_options.add_argument(
        "-l",
        "--with-license-file",
        action="store_true",
        default=config_from_file.get("with-license-file", False),
        help="dump with location of license file and "
        "contents, most useful with JSON output. "
        "For structured formats (CSV, Markdown, reST), "
        "see README for workflow examples.",
    )
    license_file_options.add_argument(
        "--with-license-files",
        action="store_true",
        default=config_from_file.get("with-license-files", False),
        help="dump with location of each license file and contents, most useful with JSON output",
    )
    license_file_options.add_argument(
        "--no-license-path",
        action="store_true",
        default=config_from_file.get("no-license-path", False),
        help="I|when specified together with option -l, "
        "suppress location of license file output",
    )
    license_file_options.add_argument(
        "--no-file-paths",
        action="store_true",
        default=config_from_file.get("no-file-paths", False),
        help="I|Suppress location of file path outputs",
    )
    license_file_options.add_argument(
        "--with-notice-file",
        action="store_true",
        default=config_from_file.get("with-notice-file", False),
        help="I|when specified together with option -l, "
        "dump with location of up to one notice file and contents",
    )
    license_file_options.add_argument(
        "--with-notice-files",
        action="store_true",
        default=config_from_file.get("with-notice-files", False),
        help="I|when specified together with option -l, "
        "dump with location of all notice files and contents",
    )
    license_file_options.add_argument(
        "--with-other-files",
        action="store_true",
        default=config_from_file.get("with-other-files", False),
        help="I|when specified together with option -l"
        " or --with-license-files, dump with location"
        " of other licensing-related files and contents",
    )
    format_options.add_argument(
        "--filter-strings",
        action="store_true",
        default=config_from_file.get("filter-strings", False),
        help="filter input according to code page",
    )
    format_options.add_argument(
        "--filter-code-page",
        action="store",
        type=str,
        default=config_from_file.get("filter-code-page", "latin1"),
        metavar="CODE",
        help="I|specify code page for filtering (default: %(default)s)",
    )

    verify_options.add_argument(
        "--fail-on",
        action="store",
        type=str,
        default=config_from_file.get("fail-on", None),
        help="fail (exit with code 1) on the first occurrence "
        "of the licenses of the semicolon-separated list",
    )
    verify_options.add_argument(
        "--allow-only",
        action="store",
        type=str,
        default=config_from_file.get("allow-only", None),
        help="fail (exit with code 1) on the first occurrence "
        "of the licenses not in the semicolon-separated list",
    )
    verify_options.add_argument(
        "--partial-match",
        action="store_true",
        default=config_from_file.get("partial-match", False),
        help="enables partial matching for --allow-only/--fail-on",
    )

    return parser


def output_colored(code: str, text: str, is_bold: bool = False) -> str:
    """
    Create function to output with color sequence
    """
    if is_bold:
        code = f"1;{code}"

    return f"\033[{code}m{text}\033[0m"


def save_if_needs(output_file: str | None, output_string: str) -> None:
    """
    Save to path given by args
    """
    if output_file is None:
        return

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output_string)
            if not output_string.endswith("\n"):
                # Always end output files with a new line
                f.write("\n")

        sys.stdout.write(f"created path: {output_file}\n")
        sys.exit(0)
    except OSError:
        sys.stderr.write("check path: --output-file\n")
        sys.exit(1)


def main() -> None:  # pragma: no cover
    parser = create_parser()
    args = parser.parse_args()

    output_string = create_output_string(args)

    output_file = args.output_file
    save_if_needs(output_file, output_string)

    print(output_string)
    warn_string = create_warn_string(args)
    if warn_string:
        print(warn_string, file=sys.stderr)


if __name__ == "__main__":  # pragma: no cover
    main()
