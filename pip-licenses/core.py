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
    __version__,
    __summary__,
    annotations,
    TYPE_CHECKING,
    deduplicate_and_normalize,
    DEFAULT_OUTPUT_FIELDS,
    FIELD_NAMES,
    LEGACY_AUTHORS_BY_FILE_PATTERN,
    LEGACY_LICENSE_BY_FILE_PATTERN,
    LEGACY_NOTICE_BY_FILE_PATTERN,
    LICENSE_UNKNOWN,
    normalize_pkg_name_and_version,
    normalize_pkg_name,
    SUMMARY_FIELD_NAMES,
    SUMMARY_OUTPUT_FIELDS,
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
from importlib.metadata import Distribution

from .cli import (
    pseudoChoices,
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


def extract_homepage(metadata: Message) -> Union[str, None]:
    """Extracts a homepage attribute from the package metadata.

    Retrieve home page from the PEP 753 `Project-URL` metadata.
    As a fallback, try the Core Metadata 1.0 home-page attribute.
    If all else fails, try other PEP 753 `Project-URL` labels.

    Args:
        metadata: The package metadata to extract the home page from.

    Returns:
        The home page if applicable, None otherwise.
    """

    candidates: dict[str, str] = {}

    for entry in metadata.get_all(PEP735_URL_KEY, []):
        key, value = entry.split(",", 1)
        candidates[key.strip().lower()] = value.strip()

    # start with Core Metadata 1.2 (PEP 753)
    # https://packaging.python.org/en/latest/specifications/core-metadata/#core-metadata-project-url
    homepage = candidates.get(KNOWN_URL_SUB_KEYS[0])
    if homepage is not None:
        return homepage

    # fall back to deprecated Core Metadata 1.0
    # https://packaging.python.org/en/latest/specifications/core-metadata/#home-page
    homepage = metadata.get(FALLBACK_URL_KEY, None)
    if homepage is not None:
        return homepage

    # if all else fails, try alternative Core Metadata 1.2 labels
    # https://packaging.python.org/en/latest/specifications/well-known-project-urls/#well-known-labels
    for priority_key in KNOWN_URL_SUB_KEYS[1:-1]:
        if priority_key in candidates:
            return candidates[priority_key]

    return None


METADATA_KEYS: dict[str, list[Callable[[Message], Union[str, None]]]] = {
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
    "license_expression": [
        lambda metadata: metadata.get("license-expression")
    ],
    "summary": [lambda metadata: metadata.get("summary")],
}

def _get_pkg_included_file(
        pkg: Distribution, file_names_rgx: str
    ) -> tuple[str, str]:
    """
    Attempt to find the package's included file on disk and return the
    tuple (included_file_path, included_file_contents).
    """
    included_file = LICENSE_UNKNOWN
    included_text = LICENSE_UNKNOWN

    pkg_files = pkg.files or ()
    pattern = re.compile(file_names_rgx)
    matched_rel_paths = filter(
        lambda file: pattern.match(file.name), pkg_files
    )
    for rel_path in matched_rel_paths:
        abs_path = Path(str(pkg.locate_file(rel_path)))
        if not abs_path.is_file():
            continue
        included_file = str(abs_path)
        with open(
            abs_path, encoding="utf-8", errors="backslashreplace"
        ) as included_file_handle:
            included_text = included_file_handle.read()
        break
    return (included_file, included_text)


def _get_pkg_info(*args, **kwargs) -> dict[str, Union[str, list[str]]]:
    pkg: Distribution = None
    if len(args) > 0 and isinstance(args[0], Distribution):
        pkg = cast(Distribution, args[0])
        args = args[1:]
    else:
        pkg = kwargs.pop("pkg", None)
    if not isinstance(pkg, Distribution):  # defensive code to support runtime typing
        raise TypeError("[CWE-573] pkg must be a Distribution") from None

    license_file, license_text = _get_pkg_included_file(
        pkg,
        LEGACY_LICENSE_BY_FILE_PATTERN,
    )
    notice_file, notice_text = _get_pkg_included_file(pkg, LEGACY_NOTICE_BY_FILE_PATTERN)
    other_file, other_text = _get_pkg_included_file(
        pkg,
        LEGACY_AUTHORS_BY_FILE_PATTERN,
    )
    pkg_info: dict[str, Union[str, list[str]]] = {
        "name": pkg.metadata["name"],
        "version": pkg.version,
        "namever": "{} {}".format(pkg.metadata["name"], pkg.version),
        "licensefile": license_file,
        "licensetext": license_text,
        "noticefile": notice_file,
        "noticetext": notice_text,
        "otherfile": other_file,
        "othertext": other_text,
    }
    metadata = pkg.metadata
    for field_name, field_selector_fns in METADATA_KEYS.items():
        value = None
        for field_selector_fn in field_selector_fns:
            # Type hint of `Distribution.metadata` states `PackageMetadata`
            # but it's actually of type `email.Message`
            value = field_selector_fn(metadata)  # type: ignore[arg-type]
            if value:
                break
        pkg_info[field_name] = value or LICENSE_UNKNOWN

    classifiers: list[str] = metadata.get_all("classifier", [])
    pkg_info["license_classifier"] = find_license_from_classifier(
        classifiers
    )

    if args.filter_strings:

        def filter_string(item: str) -> str:
            return item.encode(
                args.filter_code_page, errors="ignore"
            ).decode(args.filter_code_page)

        for k, v in pkg_info.items():
            if isinstance(v, list):
                pkg_info[k] = list(map(filter_string, v))
            else:
                pkg_info[k] = filter_string(cast(str, v))

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
    if not license_expression or license_expression != LICENSE_UNKNOWN:
        return {license_expression}

    license_classifier_set = set(license_classifier) or {LICENSE_UNKNOWN}
    if (
        from_source == FromArg.CLASSIFIER
        or from_source == FromArg.MIXED
        and len(license_classifier) > 0
    ):
        return license_classifier_set
    else:
        return {license_meta}


def get_packages(
    args: CustomNamespace,
) -> Iterator[dict[str, Union[str, list[str]]]]:

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
