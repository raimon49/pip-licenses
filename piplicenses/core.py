#!/usr/bin/env python
# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et
"""
pip-licenses.core

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
    __pkgname__,
    __version__,  # noqa: F401 -- Re-export as part of data API
    TYPE_CHECKING,  # noqa: F401 -- Re-export as part of our internal typing API
    deduplicate_and_normalize,
    LEGACY_AUTHORS_BY_FILE_PATTERN,
    LEGACY_LICENSE_BY_FILE_PATTERN,
    LEGACY_NOTICE_BY_FILE_PATTERN,
    LICENSE_BY_OTHER_FILE_PATTERN,
    LICENSE_UNKNOWN,
    normalize_pkg_name_and_version,
    normalize_pkg_name,
    FILE_MISSING,
)


import sys

# for typing
from email.message import Message
from typing import (
    cast,
    Union,
)
# NullableStr = Union[str, None]
# strs = Union[str, list[str]]
from collections.abc import Callable, Iterator
from importlib import metadata as importlib_metadata
from importlib.metadata import (
    Distribution,
    PackagePath,
)

from .cli import (
    FromArg,
    CustomNamespace,
)

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


def extract_urls(metadata: Message) -> dict[str, Union[str, list[str], None]]:
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
    _urls: dict[str, Union[str, list[str], None]] = {}
    for entry in metadata.get_all(PEP735_URL_KEY, []):
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


def extract_homepage(metadata: Message) -> Union[str, None]:
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
    candidates: dict[str, Union[str, list[str], None]] = extract_urls(metadata)

    def _help_get_first_of_many(
        raw_input: Union[str, list[str], None],
    ) -> Union[str, None]:
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
    homepage = candidates.get(KNOWN_URL_SUB_KEYS[0])
    if homepage is not None:
        return _help_get_first_of_many(homepage)

    # fall back to deprecated Core Metadata 1.0
    # https://packaging.python.org/en/latest/specifications/core-metadata/#home-page
    homepage = metadata.get(FALLBACK_URL_KEY, None)
    if homepage is not None:
        return _help_get_first_of_many(homepage)

    _has_something_flag = False
    # if all else fails, try alternative Core Metadata 1.2 labels
    # https://packaging.python.org/en/latest/specifications/well-known-project-urls/#well-known-labels
    for priority_key in KNOWN_URL_SUB_KEYS[1:]:
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


# placeholder for something like
#Value: TypeAlias = Union[str, list[str], dict[str, Union[str, list[str], NoneType]], NoneType]


METADATA_KEYS: dict[
    str,
    list[
        Callable[
            [Message],
            Union[str, list[str], dict[str, Union[str, list[str], None]], None],
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
    "license_classifier": [extract_license_from_classifiers],  # added in v6.0
    "license_expression": [
        lambda metadata: metadata.get("license-expression")
    ],
    "license_files": [lambda metadata: metadata.get_all("License-File", [])],   # added in v6.0
    "summary": [lambda metadata: metadata.get("summary")],
    "urls": [extract_urls],  # added in v6.0
}

def _get_pkg_included_file(
        pkg: Distribution, file_names_rgx: str
    ) -> tuple[str, str]:
    """
    Attempt to find the package's included file on disk and return the
    tuple (included_file_path, included_file_contents).
    """
    included_file = FILE_MISSING
    included_text = LICENSE_UNKNOWN
    matched_rel_paths = _filter_pkg_included_paths(pkg, file_names_rgx)

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


def filter_string(item: str) -> str:
    try:
        # TODO: this needs improved
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


def _do_filter_iteration(
    sub_item: Union[str, list[str], dict[str, Union[str, list[str], None]]],
) -> Union[str, list[str], dict[str, Union[str, list[str], None]]]:
    if isinstance(sub_item, list):
        return list(map(filter_string, sub_item))
    elif isinstance(sub_item, dict):
        _filtered_subset: dict[str, Union[str, list[str], None]] = (
            sub_item.copy()
        )
        for k, v in sub_item.items():
            if v is not None:  # Prune None values
                _filtered_subset[k] = _do_filter_iteration(v)  # type: ignore[assignment]
        return _filtered_subset
    else:
        return filter_string(cast(str, sub_item))


def _get_pkg_info(*args, **kwargs) ->  dict[str, Union[str, list[str], dict[str, Union[str, list[str], None]]]]:
    pkg: Distribution = None
    if len(args) > 0 and isinstance(args[0], Distribution):
        pkg = cast(Distribution, args[0])
        args = args[1:]
    else:
        pkg = kwargs.pop("pkg", None)
    if not isinstance(pkg, Distribution):  # defensive code to support runtime typing
        raise TypeError("[CWE-573] pkg must be a Distribution") from None
    pkg_name: str = pkg.metadata["name"]
    normal_pkg_name = normalize_pkg_name(pkg_name)
    legacy_info = fallback_license_retrieval(pkg)
    pkg_info: dict[
        str, Union[str, list[str], dict[str, Union[str, list[str], None]]]
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
        pkg_texts: Union[list[Union[str, None]], None] = (
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
        pkg_info["other_files"] = list(
            _filter_pkg_included_files(pkg, LICENSE_BY_OTHER_FILE_PATTERN),
        )
        pkg_other_texts: Union[list[Union[str, None]], None] = (
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
        for key, val in pkg_info.items():
            if val is not None:  # ignore top-level None values
                pkg_info[key] = _do_filter_iteration(val)

    return pkg_info


def _get_python_sys_path(executable: str) -> list[str]:
    script = "import sys; print(' '.join(filter(bool, sys.path)))"
    output = subprocess.run(
        [executable, "-c", script],
        capture_output=True,
        env={**os.environ, "PYTHONPATH": "", "VIRTUAL_ENV": ""},
        check=False,
    )
    return output.stdout.decode().strip().split()


def _filter_pkg_included_paths(
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


def _filter_pkg_included_files(
    pkg: Distribution, file_names_rgx: str
) -> set[str]:
    """
    Attempt to find the set of package's matching files included on-disk.

    Matching pathstrings are returned as relative paths to the package on-disk.
    """
    matched_rel_paths = _filter_pkg_included_paths(pkg, file_names_rgx)
    included_files_set: set[str] = set()
    for rel_path in matched_rel_paths:
        abs_path = Path(str(pkg.locate_file(rel_path)))
        if not abs_path.is_file():
            continue  # pragma: no cover
        included_file = str(rel_path)
        included_files_set.add(included_file)

    return included_files_set


def get_pkg_license_texts_from_disk(
    pkg: Distribution, filelist: Union[list[Union[str, None]], None] = None
) -> Union[list[Union[str, None]], None]:
    if filelist:
        license_texts = []
        for a_license_file in filelist:
            if a_license_file:
                _fh, a_license_file_text = _get_pkg_included_file(
                    pkg, a_license_file
                )
                if _fh:
                    license_texts.append(a_license_file_text)
        return license_texts
    return None


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
    # TODO: 242 -- fix case of from mixed where license expression is present && other values are too.
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


# TODO: cleanup fix for GHI-309 (DO NOT MERGE YET)
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
    license_file, license_text = _get_pkg_included_file(
        pkg, LEGACY_LICENSE_BY_FILE_PATTERN
    )
    notice_file, notice_text = _get_pkg_included_file(
        pkg, LEGACY_NOTICE_BY_FILE_PATTERN
    )
    author_file, author_text = _get_pkg_included_file(
        pkg, LEGACY_AUTHORS_BY_FILE_PATTERN
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


def get_packages(
    args: CustomNamespace,
) -> Iterator[dict[str, Union[str, list[str], dict[str, Union[str, list[str], None]]]]]:

    if args.python == sys.executable:
        search_paths = sys.path
    else:
        search_paths = _get_python_sys_path(args.python)

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

        pkg_info = _get_pkg_info(pkg, kwargs=args)

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
