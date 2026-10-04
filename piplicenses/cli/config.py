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

# See https://github.com/raimon49/pip-licenses/issues/360
# should just bridge this import
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
    sys,
)

# See https://docs.python.org/3/library/argparse.html
from ._argparse_bridge import argparse
from .pseudo_choices import (
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


def _split_legacy_tokens(value: str) -> list[str]:
    """
    Split a serialized value on unescaped LEGACY_TOKEN occurrences.

    A backslash escapes either LEGACY_TOKEN or another backslash:

    >>> LEGACY_TOKEN = ";"
    >>> _split_legacy_tokens(r"a\\;b;c")
    ['a;b', 'c']
    """
    if not LEGACY_TOKEN:
        raise ValueError("LEGACY_TOKEN must be non-empty")

    if "\\" in LEGACY_TOKEN:
        raise ValueError(
            "LEGACY_TOKEN must not contain a backslash when using escaping"
        )

    parts: list[str] = []
    current: list[str] = []
    index = 0

    while index < len(value):
        if value[index] == "\\":
            escaped_token_start = index + 1

            if value.startswith(LEGACY_TOKEN, escaped_token_start):
                current.append(LEGACY_TOKEN)
                index += 1 + len(LEGACY_TOKEN)
            elif value.startswith("\\", escaped_token_start):
                current.append("\\")
                index += 2
            else:
                # Preserve an unrecognized escape literally.
                current.append("\\")
                index += 1

        elif value.startswith(LEGACY_TOKEN, index):
            parts.append("".join(current))
            current.clear()
            index += len(LEGACY_TOKEN)

        else:
            current.append(value[index])
            index += 1

    parts.append("".join(current))
    return parts


def _normalize_as_set(
    value: Union[Iterable[str], str, bytes, None],
) -> set[str]:
    """
    Normalize a string, bytes value, or iterable into a set of strings.

    String and bytes values are treated as serialized values. Unescaped
    LEGACY_TOKEN occurrences separate values, while backslash-escaped
    LEGACY_TOKEN occurrences are interpreted literally. Backslashes can
    themselves be escaped with another backslash.

    Empty fields are discarded when a serialized value contains
    LEGACY_TOKEN, matching the original behavior.

    >>> LEGACY_TOKEN = ";"
    >>> _normalize_as_set("alpha;beta")
    {'alpha', 'beta'}

    >>> _normalize_as_set("alpha\\;beta;gamma") # TODO: may need raw string and doc escapes?
    {'alpha;beta', 'gamma'}

    >>> _normalize_as_set(r"c:\\path;d")
    {'c:\\path', 'd'}

    >>> _normalize_as_set(None)
    set()

    >>> _normalize_as_set(["alpha", None, 42])
    {'alpha', '42'}
    """
    if value is None:
        return set()
    if isinstance(value, (str, bytes)):
        _wrapped_value = str(value)
        if LEGACY_TOKEN in _wrapped_value:
            return set(
                filter(
                    None, map(str.strip, _split_legacy_tokens(_wrapped_value))
                )
            )
        return {_wrapped_value}
    try:
        return {str(x) for x in value if x is not None}
    except TypeError:
        return {str(value)}


def _serialize_to_semi_str(value: Iterable[str]) -> str:
    """
    Serialize an iterable of strings for use with _normalize_as_set().

    LEGACY_TOKEN and backslashes are escaped with a backslash. Members are
    sorted to produce deterministic output. Since _normalize_as_set()
    strips fields and discards empty fields in serialized values, members
    must not have leading or trailing whitespace.

    The empty set is represented by LEGACY_TOKEN itself; splitting it
    produces only empty fields, which are discarded.

    >>> LEGACY_TOKEN = ";"
    >>> serialized = serialize_to_semi_str({"beta", "alpha"})
    >>> serialized
    'alpha;beta'
    >>> _normalize_as_set(serialized)
    {'alpha', 'beta'}

    >>> serialized = serialize_to_semi_str({"alpha;beta", r"c:\tmp"})
    >>> _normalize_as_set(serialized)
    {'alpha;beta', 'c:\\tmp'}

    >>> serialize_to_semi_str(set()) == LEGACY_TOKEN
    True
    >>> _normalize_as_set(serialize_to_semi_str(set()))
    set()

    >>> serialize_to_semi_str({" leading"})
    Traceback (most recent call last):
        ...
    ValueError: Set members must not have leading or trailing whitespace
    """
    if not LEGACY_TOKEN:
        raise ValueError("LEGACY_TOKEN must be non-empty")

    if "\\" in LEGACY_TOKEN:
        raise ValueError(
            "LEGACY_TOKEN must not contain a backslash when using escaping"
        )

    # TODO: probably should use an internal helper function to "normalize" the whitespace
    # but for now just use simple strip() (e.g., ignore the whitespace)
    members = (
        {value.strip(f"{LEGACY_TOKEN} ")}
        if isinstance(value, str)
        else {str(item).strip(f"{LEGACY_TOKEN} ") for item in value}
    )

    def _escape(member: str) -> str:
        # Escape backslashes first so newly added escapes are not escaped
        # again when LEGACY_TOKEN is escaped.
        return member.replace("\\\\", "\\").replace(
            LEGACY_TOKEN,
            "\\" + LEGACY_TOKEN,
        )

    if not members:
        return LEGACY_TOKEN

    return LEGACY_TOKEN.join(_escape(member) for member in sorted(members))


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
    include_from_system: bool = False
    with_urls: bool = False
    if "6.0" in __version__:
        with_description: bool = False  # DEPRECIATED in v6.1+
    else:
        with_descriptions: bool = False
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
        without_file_paths: bool = False  # (TODO: use --without-paths)
    with_authors: bool = False
    with_maintainers: bool = False  # added in v6.0
    if "6.0" in __version__:
        with_notice_file: bool = False  # DEPRECIATED in v6.1
    with_notice_files: bool = False  # added in v6.0 (as boolean)
    with_other_files: bool = False  # added in v6.0 (as boolean)
    without_notice_paths: bool = False  # added in v6.0
    without_other_paths: bool = False  # added in v6.0
    # placeholder -- for with/without authors stuff
    filter_strings: bool = False
    partial_match: bool = False
    # removed no_version: bool = False  # DEPRECIATED in v6.1+
    without_versions: bool = False
    # string / optional values
    output_file: Optional[str] = None
    filter_code_page: Optional[str] = None
    # paths
    python: str = DEFAULT_PYTHON

    # sequence values
    fail_on: Optional[set] = field(default_factory=set)
    allow_only: Optional[set] = field(default_factory=set)
    ignore_packages: set[str] = field(default_factory=set)
    packages: set[str] = field(default_factory=set)
    warn_on: set[str] = field(default_factory=set)
    allow_packages: set[str] = field(default_factory=set)

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
        if not isinstance(self.fail_on, set):
            self.fail_on = self._normalize_to_set(self.fail_on)
        if not isinstance(self.allow_only, set):
            self.allow_only = self._normalize_to_set(self.allow_only)
        if not isinstance(self.allow_packages, set):
            self.allow_packages = self._normalize_to_set(self.allow_packages)
        if not isinstance(self.warn_on, set):
            self.warn_on = self._normalize_to_set(self.warn_on)

    @staticmethod
    def _normalize_to_set(value: Union[Iterable[str], str, None]) -> set[str]:
        if value is None:
            return set()
        return _normalize_as_set(value)

    @staticmethod
    def _serialize_to_semi_str(value: Union[Iterable[str], None]) -> str:
        if value is None:
            return ""
        return _serialize_to_semi_str(value)

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

        _with_descriptions_map = [
            "with_description",
            "with_descriptions",
        ]

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
            "without_versions",
        ]

        _ignore_packages_map = [
            "ignore_package",
            "ignore_packages",
        ]

        _fail_on_map = [
            "fail_on_str",
            "fail_on",
        ]

        _allow_only_map = [
            "allow_only_str",
            "allow_only",
        ]

        _pre_processed_name: str = name.strip().lower()

        for _mapping in (
            _with_descriptions_map,
            _with_license_files_map,
            _with_notice_files_map,
            _without_license_paths_map,
            _without_file_paths_map,
            _without_version_map,
            _ignore_packages_map,
            _fail_on_map,
            _allow_only_map,
        ):
            if _pre_processed_name in _mapping:
                if (
                    not "6.0" in __version__
                ) and _pre_processed_name in _mapping[:-2]:
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
            "include_from_system",
            "with_authors",
            "with_maintainers",
            "with_urls",
            "with_description"
            if "6.0." in __version__
            else "with_descriptions",
            "with_license_files",
            "with_notice_files",
            "with_other_files",
            "without_license_paths",
            "without_notice_paths",
            "without_other_paths",
            "without_file_paths",
            "filter_strings",
            "partial_match",
            "without_versions",
        }
        sets = {
            "ignore_packages",
            "packages",
            "allow_packages",
            "warn_on",
            "fail_on",
            "allow_only",
        }

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

    @property
    def allow_packages_set(self) -> set[str]:
        return set(self.allow_packages or set())

    @allow_packages_set.setter
    def allow_packages_set(self, value: Union[Iterable[str], None]) -> None:
        self.allow_packages = self._normalize_to_set(value)

    @property
    def allow_only_set(self) -> set[str]:
        return set(self.allow_only or set())

    @allow_only_set.setter
    def allow_only_set(self, value: Union[Iterable[str], None]) -> None:
        self.allow_only = self._normalize_to_set(value)

    @property
    def fail_on_set(self) -> set[str]:
        return set(self.fail_on or set())

    @fail_on_set.setter
    def fail_on_set(self, value: Union[Iterable[str], None]) -> None:
        self.fail_on = self._normalize_to_set(value)

    @property
    def with_license_paths(self) -> bool:
        return self.without_license_paths is False

    @with_license_paths.setter
    def with_license_paths(self, value: Union[bool, None]) -> None:
        self.without_license_paths = value is False

    @property
    def with_notice_paths(self) -> bool:
        return self.without_notice_paths is False

    @with_notice_paths.setter
    def with_notice_paths(self, value: Union[bool, None]) -> None:
        self.without_notice_paths = value is False

    @property
    def with_other_paths(self) -> bool:
        return self.without_other_paths is False

    @with_other_paths.setter
    def with_other_paths(self, value: Union[bool, None]) -> None:
        self.without_other_paths = value is False

    if "6.1" in __version__:
        # DEPRECIATED in v6.0; use without_* instead.
        @property  # type: ignore[no-redef]
        def no_version(self) -> bool:
            """DEPRECIATED in v6.1; use without_versions instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use without_versions instead.",
                stacklevel=2,
            )
            return self.without_versions

        # DEPRECIATED in v6.0; use without_* instead.
        @no_version.setter
        def no_version(self, value: Union[bool, None]) -> None:
            """DEPRECIATED in v6.1; use without_versions instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use without_versions instead.",
                stacklevel=2,
            )
            self.without_versions = value is True

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

        # DEPRECIATED in v6.0; use without_* instead.
        @property  # type: ignore[no-redef]
        def with_description(self) -> bool:
            """DEPRECIATED in v6.1; use with_descriptions instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use with_descriptions instead.",
                stacklevel=2,
            )
            return self.with_descriptions

        # DEPRECIATED in v6.0; use without_* instead.
        @with_description.setter
        def with_description(self, value: Union[bool, None]) -> None:
            """DEPRECIATED in v6.1; use with_descriptions instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use with_descriptions instead.",
                stacklevel=2,
            )
            self.with_descriptions = value is True

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
        # DEPRECIATED in v6.0; use allow_only instead.
        @property
        def allow_only_str(self) -> str:
            return self._serialize_to_semi_str(self.allow_only or None)

        # DEPRECIATED in v6.0; use allow_only instead.
        @allow_only_str.setter
        def allow_only_str(
            self, value: Union[Iterable[str], str, None]
        ) -> None:
            self.allow_only = self._normalize_to_set(value)

        # DEPRECIATED in v6.0; use fail_on instead.
        @property
        def fail_on_str(self) -> str:
            return self._serialize_to_semi_str(self.fail_on or None)

        # DEPRECIATED in v6.0; use fail_on instead.
        @fail_on_str.setter
        def fail_on_str(self, value: Union[Iterable[str], str, None]) -> None:
            self.fail_on = self._normalize_to_set(value)

        @property  # type: ignore[no-redef]
        def no_version(self) -> bool:
            """DEPRECIATED in v6.1; use without_versions instead."""
            import warnings

            warnings.warn(
                "WILL BE DEPRECIATED in v6.1; use without_versions instead."
                "This will be an error in the future."
                "See https://github.com/raimon49/pip-licenses/issues/349",
                stacklevel=2,
            )
            return self.without_versions

        # DEPRECIATED in v6.0; use without_* instead.
        @no_version.setter
        def no_version(self, value: Union[bool, None]) -> None:
            """DEPRECIATED in v6.1; use without_versions instead."""
            import warnings

            warnings.warn(
                "WILL BE DEPRECIATED in v6.1; use without_versions instead."
                "This will be an error in the future."
                "See https://github.com/raimon49/pip-licenses/issues/349",
                stacklevel=2,
            )
            self.without_versions = value is True

        # DEPRECIATED in v6.0; use include_from_system instead.
        @property  # type: ignore[no-redef]
        def with_system(self) -> bool:
            """DEPRECIATED in v6.0; use include_from_system instead."""
            import warnings

            warnings.warn(
                "DEPRECIATED in v6.0; use include_from_system instead."
                "This will be an error in the future.",
                stacklevel=2,
            )
            return self.include_from_system

        # DEPRECIATED in v6.0; use include_from_system instead.
        @with_system.setter
        def with_system(self, value: Union[bool, None]) -> None:
            """DEPRECIATED in v6.0; use include_from_system instead."""
            import warnings

            warnings.warn(
                "DEPRECIATED in v6.0; use include_from_system instead."
                "This will be an error in the future."
                "See https://github.com/raimon49/pip-licenses/issues/349",
                stacklevel=2,
            )
            self.include_from_system = value is True

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

        # added in v6.0
        @property  # type: ignore[no-redef]
        def with_descriptions(self) -> bool:
            """ADDED in v6.0; Same as with_description.

            Previous to v6.0 there was no standardization of what are now:
            with/without prefixes.
            """
            return self.with_description

        # added in v6.0
        @with_descriptions.setter
        def with_descriptions(self, value: Union[bool, None]) -> None:
            """ADDED in v6.0; Same as with_description.

            Previous to v6.0 there was no standardization of what are now:
            with/without prefixes.
            """
            self.with_description = value is True


CustomNamespace = Configuration
"""DEPRECIATED in v6.0; use piplicenses.cli.config.Configuration instead."""


__all__ = [
    """Configuration""",
    """CustomNamespace""",  # DEPRECIATED in v6.0+
]
