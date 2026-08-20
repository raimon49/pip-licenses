# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et

# pip-licenses.cli.config
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


"""pip-licenses.cli.config

To be documented.
"""

from collections.abc import Iterable
from dataclasses import (
    dataclass,
    field,
)
from typing import (
    # See https://github.com/raimon49/pip-licenses/issues/360
    Any,
    # NullableStr = Union[str, None]
    Optional,
    # strs = Union[str, list[str]]
    # _oneOrMoreStrs = Union[str, list[str]]
    # _zeroOrMoreStrs = Union[str, list[NullableStr], None]
    Union,
)

from . import (
    LEGACY_TOKEN,
    __pkgname__,  # noqa: F401 -- Re-export as part of data API
    __version__,
    argparse,
    sys,
)
from .pseudoChoices import (
    FormatArg,
    FromArg,
    OrderArg,
)

if "6.1" in __version__:
    import warnings


NullableStr = Union[str, None]
"""Explicitly required (e.g., not optional) value of type string, but can be set to None.

Because the value is required even if intentionally empty, we allow
None (e.g. nullified `\0` value) to be treated as a zero length null-terminated (empty) string.
The type is not intended to be any kind of union semantically, only syntacticly for mypy.

This is an internal type and is _not_ part of the public API. (convert to `type(str())` for that)

See https://github.com/raimon49/pip-licenses/issues/360
"""


DEFAULT_PYTHON: str = f"{sys.executable}"
"""The default python for this piplicenses.cli.

Should be the same as executable that imported piplicenses.cli.
e.g., sys.executable
"""


def _normalize_as_set(
    value: Union[Iterable[str], str, bytes, None],
) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, (str, bytes)):
        _wrapped_value = str(value)
        if LEGACY_TOKEN in _wrapped_value:
            return set(
                filter(
                    None, map(str.strip, _wrapped_value.split(LEGACY_TOKEN))
                )
            )
        return {_wrapped_value}
    try:
        return {str(x) for x in value if x is not None}
    except TypeError:
        return {str(value)}


# Descriptor that normalizes assigned iterables into a set[str].
class SetOfStr:
    """
    Descriptor that stores a set of strings per-instance and accepts assignment
    from any iterable of strings (list, tuple, frozenset, set, etc.). Assigning
    None will result in an empty set.

    Storage is kept in instance.__dict__ under a private name computed by
    __set_name__.
    """

    def __init__(self, name: Union[str, None] = None) -> None:
        # optional human name, will be set by __set_name__
        self._name = name

    def __set_name__(self, owner: type[Any], name: str) -> None:
        # store the private attribute name to use on the instance
        self._name = f"_{name}"

    def __get__(
        self,
        instance: Optional[Any],  # noqa: ANN401 -- Dynamically typed at runtime
        owner: Optional[type[Any]] = None,
    ) -> Any:  # noqa: ANN401 -- Dynamically typed
        if instance is None:
            # Accessed on the class: return descriptor itself (useful for introspection)
            return self
        return instance.__dict__.get(self._name, set())

    def __set__(
        self,
        instance: Any,  # noqa: ANN401 -- Dynamically typed at runtime
        value: Optional[Union[Iterable[str], str, bytes]],
    ) -> None:
        # Accept None -> empty set
        # but, if value already a set-like, convert so we guarantee set[str]
        normalized = set() if value is None else _normalize_as_set(value)
        instance.__dict__[self._name] = normalized

    def __delete__(
        self,
        instance: Any,  # noqa: ANN401 -- Dynamically typed at runtime
    ) -> None:
        instance.__dict__.pop(self._name, None)


@dataclass
class Configuration(argparse.Namespace):
    # enum-like values (may be None? until argparse sets them)
    from_: FromArg = FromArg.MIXED
    order: OrderArg = OrderArg.NAME
    format_: FormatArg = FormatArg.PLAIN

    # flags / booleans -- default to False (behave as if option omitted)
    summary: bool = False
    with_system: bool = False
    with_urls: bool = False
    with_description: bool = False
    if "6.0" in __version__:
        with_license_file: bool = False  # DEPRECIATED in v6.1+
    with_license_files: bool = False  # added in v6.0
    if "6.0" in __version__:
        no_license_path: bool = False  # DEPRECIATED in v6.1+
    else:
        without_license_paths: bool = (
            False  # (TODO: use --without-license-path|--without-paths)
        )
    if "6.0" in __version__:
        no_file_paths: bool = False  # DEPRECIATED in v6.1+
    else:
        without_file_paths: bool = (
            False  # (TODO: use --without-license-path|--without-paths)
        )
    with_authors: bool = False
    with_maintainers: bool = False  # added in v6.0
    if "6.0" in __version__:
        with_notice_file: bool = False  # DEPRECIATED in v6.1+
    with_notice_files: bool = False  # added in v6.0
    with_other_files: bool = False  # added in v6.0
    filter_strings: bool = False
    partial_match: bool = False
    if "6.0" in __version__:
        no_version: bool = False  # DEPRECIATED in v6.1+
    else:
        without_version: bool = (
            False  # (TODO: use --without-license-path|--without-paths)
        )
    # string / optional values
    output_file: Optional[str] = None
    filter_code_page: Optional[str] = None
    fail_on: Optional[str] = (
        None  # DEPRECIATED in v6.0+ (TODO: will need to handle lists)
    )
    allow_only: Optional[str] = (
        None  # DEPRECIATED in v6.0+ (TODO: will need to handle lists)
    )
    python: str = DEFAULT_PYTHON

    # sequence values
    ignore_packages: set[str] = field(default_factory=set)
    packages: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        # Ensure values passed via __init__ are normalized to sets. Dataclass __init__
        # will assign the provided values which will call our descriptor if the
        # descriptor replaces these attributes on the class (see module-level replacement
        # below). For safety (e.g., if descriptor replacement has not yet occurred),
        # normalize here too.
        # Accept None, lists, tuples, frozensets, etc.
        if not isinstance(self.ignore_packages, set):
            self.ignore_packages = self._normalize_to_set(self.ignore_packages)
        if not isinstance(self.packages, set):
            self.packages = self._normalize_to_set(self.packages)

    @staticmethod
    def _normalize_to_set(value: Union[Iterable[str], None]) -> set[str]:
        if value is None:
            return set()
        return _normalize_as_set(value)

    @classmethod
    def from_namespace(cls, ns: argparse.Namespace) -> "Configuration":
        """
        Safely construct a Configuration from an argparse.Namespace (or
        anything compatible with vars()).
        """
        # vars(ns) will contain all attributes argparse set.
        # We pass them into the dataclass constructor. Extra keys are expected to
        # match the dataclass fields; argparse sets only known dests from add_argument.
        return cls(**vars(ns))

    def to_namespace(self) -> argparse.Namespace:
        """
        Convert back to a plain argparse.Namespace (useful if some APIs still
        expect Namespace instances).
        """
        ns = argparse.Namespace()
        for k, v in vars(self).items():
            setattr(ns, k, v)
        return ns

    def __substitute_attr__(self, name: str) -> str:
        """
        Provide canonicalized attribute names for this implementation.

        Namely those DEPRECIATED in v6.0+:
           * with_license_file --> with_license_files
           * with_notice_file --> with_notice_files
           * no_license_path --> without_license_paths
           * no_file_paths --> without_file_paths
        """
        # only handle if given a string
        if not isinstance(name, str):
            raise AttributeError(name) from TypeError(name)  # noqa: TRY004 -- it's both

        _with_license_files_map = [
            "with_license_file",
            "with_license_files",
        ]

        _with_notice_files_map = [
            "with_notice_file",
            "with_notice_files",
        ]

        _without_license_paths_map = [
            "no_license_path",
            "without_license_paths",
        ]

        _without_file_paths_map = [
            "no_file_paths",
            "without_file_paths",
        ]

        _without_version_map = [
            "no_version",
            "without_version",
        ]

        _ignore_packages_map = [
            "ignore_package",
            "ignore_packages",
        ]

        _pre_processed_name: str = name.strip().lower()

        for _mapping in (
            _with_license_files_map,
            _with_notice_files_map,
            _without_license_paths_map,
            _without_file_paths_map,
            _without_version_map,
            _ignore_packages_map,
        ):
            if _pre_processed_name in _mapping:
                if not "6.0" in __version__:
                    warnings.warn(
                        f"Configuration attributes have changed, e.g., {name} to {_mapping[-1]}",
                        stacklevel=2,
                    )
                return _mapping[-1]
        # Otherwise fall-through
        return name

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401 -- Dynamically typed at runtime
        """
        Provide stable fallbacks for attributes that might be missing entirely.

        - Known boolean flags return False
        - Known sequence fields return empty set for the set-backed fields
        - Otherwise return None
        """
        # Avoid infinite recursion for special attribute lookups
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)

        booleans = {
            "summary",
            "with_system",
            "with_authors",
            "with_maintainers",
            "with_urls",
            "with_description",
            "with_license_files",
            "with_notice_file",
            "with_notice_files",
            "with_other_files",
            "without_license_paths",
            "without_file_paths",
            "filter_strings",
            "partial_match",
            "without_version",
        }
        sets = {"ignore_packages", "packages"}

        _normalized_name = self.__substitute_attr__(name)

        if _normalized_name in booleans:
            return False
        if _normalized_name in sets:
            return set()
        # Generic fallback
        return None

    # convenience accessor/mutator for ignore_packages
    @property
    def ignore_packages_set(self) -> set[str]:
        return set(self.ignore_packages or set())

    @ignore_packages_set.setter
    def ignore_packages_set(self, value: Union[Iterable[str], None]) -> None:
        self.ignore_packages = self._normalize_to_set(value)

    @property
    def packages_set(self) -> set[str]:
        return set(self.packages or set())

    @packages_set.setter
    def packages_set(self, value: Union[Iterable[str], None]) -> None:
        self.packages = self._normalize_to_set(value)

    if "6.1" in __version__:
        # DEPRECIATED in v6.0; use without_* instead.
        @property  # type: ignore[no-redef]
        def no_version(self) -> bool:
            """DEPRECIATED in v6.1; use without_version instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use without_version instead.",
                stacklevel=2,
            )
            return self.without_version

        # DEPRECIATED in v6.0; use without_* instead.
        @no_version.setter
        def no_version(self, value: Union[bool, None]) -> None:
            """DEPRECIATED in v6.1; use without_version instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use without_version instead.",
                stacklevel=2,
            )
            self.without_version = value is True

        # DEPRECIATED in v6.0; use without_* instead.
        @property  # type: ignore[no-redef]
        def no_file_paths(self) -> bool:
            """DEPRECIATED in v6.1; use without_file_paths instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use without_file_paths instead.",
                stacklevel=2,
            )
            return self.without_file_paths

        # DEPRECIATED in v6.0; use without_* instead.
        @no_file_paths.setter
        def no_file_paths(self, value: Union[bool, None]) -> None:
            """DEPRECIATED in v6.1; use without_file_paths instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use no_file_paths instead.",
                stacklevel=2,
            )
            self.without_file_paths = value is True

        # DEPRECIATED in v6.0; use without_* instead.
        @property  # type: ignore[no-redef]
        def no_license_path(self) -> bool:
            """DEPRECIATED in v6.1; use without_license_paths instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use without_license_paths instead.",
                stacklevel=2,
            )
            return self.without_license_paths

        # DEPRECIATED in v6.0; use without_* instead.
        @no_license_path.setter
        def no_license_path(self, value: Union[bool, None]) -> None:
            """DEPRECIATED in v6.1; use without_license_paths instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use without_license_paths instead.",
                stacklevel=2,
            )
            self.without_license_paths = value is True

        # DEPRECIATED in v6.0; use with_*s instead.
        @property  # type: ignore[no-redef]
        def with_notice_file(self) -> bool:
            """DEPRECIATED in v6.1; use with_notice_files instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use with_notice_files instead.",
                stacklevel=2,
            )
            return self.with_notice_files

        # DEPRECIATED in v6.0; use with_*s instead.
        @with_notice_file.setter
        def with_notice_file(self, value: Union[bool, None]) -> None:
            """DEPRECIATED in v6.1; use with_notice_files instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use with_notice_files instead.",
                stacklevel=2,
            )
            self.with_notice_files = value is True

        # DEPRECIATED in v6.0; use with_*s instead.
        @property  # type: ignore[no-redef]
        def with_license_file(self) -> bool:
            """DEPRECIATED in v6.1; use with_license_files instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use with_license_files instead.",
                stacklevel=2,
            )
            return self.with_notice_files

        # DEPRECIATED in v6.0; use with_*s instead.
        @with_license_file.setter
        def with_license_file(self, value: Union[bool, None]) -> None:
            """DEPRECIATED in v6.1; use with_license_files instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use with_license_files instead.",
                stacklevel=2,
            )
            self.with_notice_files = value is True

    elif "6.0" in __version__:
        # added in v6.0
        @property  # type: ignore[no-redef]
        def without_version(self) -> bool:
            """ADDED in v6.0; Same as no_version.

            Previous to v6.0 there was no standardization of what are now:
            with/without prefixes.
            """
            return self.no_version

        # added in v6.0
        @without_version.setter
        def without_version(self, value: Union[bool, None]) -> None:
            """ADDED in v6.0; Same as no_version.

            Previous to v6.0 there was no standardization of what are now:
            with/without prefixes.
            """
            self.no_version = value is True

        # added in v6.0
        @property  # type: ignore[no-redef]
        def without_file_paths(self) -> bool:
            """ADDED in v6.0; Same as no_file_paths.

            Previous to v6.0 there was no standardization of what are now:
            with/without prefixes.
            """
            return self.no_file_paths

        # added in v6.0
        @without_file_paths.setter
        def without_file_paths(self, value: Union[bool, None]) -> None:
            """ADDED in v6.0; Same as no_file_paths.

            Previous to v6.0 there was no standardization of what are now:
            with/without prefixes.
            """
            self.no_file_paths = value is True

        # added in v6.0
        @property  # type: ignore[no-redef]
        def without_license_paths(self) -> bool:
            """ADDED in v6.0; Same as no_license_path.

            Previous to v6.0 there was no standardization of what are now:
            with/without prefixes.
            """
            return self.no_license_path

        # added in v6.0
        @without_license_paths.setter
        def without_license_paths(self, value: Union[bool, None]) -> None:
            """ADDED in v6.0; Same as no_license_path.

            Previous to v6.0 there was no standardization of what are now:
            with/without prefixes.
            """
            self.no_license_path = value is True


CustomNamespace = Configuration
"""DEPRECIATED in v6.0; use piplicenses.cli.config.Configuration instead."""


__all__ = [
    """Configuration""",
    """CustomNamespace""",  # DEPRECIATED in v6.0+
]
