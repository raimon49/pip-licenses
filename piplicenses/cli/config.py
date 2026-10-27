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
    cast,
)

from . import (
    LEGACY_TOKEN,
    __pkgname__,  # noqa: F401 -- Re-export as part of data API
    __version__,
    sys,
)

# See https://docs.python.org/3/library/argparse.html
from ._argparse_bridge import argparse
from ._flags import FORMAT_FLAG_OTHERS_GROUP
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
    r"""
    Split a serialized value on unescaped LEGACY_TOKEN occurrences.

    A backslash escapes either LEGACY_TOKEN or another backslash:

    >>> LEGACY_TOKEN = ";"
    >>> _split_legacy_tokens(r"a\;b;c")
    ['a;b', 'c']
    >>>
    >>> _split_legacy_tokens(r"a;b;c")
    ['a', 'b', 'c']
    >>>
    >>> _split_legacy_tokens(r"a;b;c;")
    ['a', 'b', 'c']
    >>>

    >>> LEGACY_TOKEN = ";"
    >>> _split_legacy_tokens(r"a;b;c;") == _split_legacy_tokens(r"a;b;c")
    True
    >>>

    >>> LEGACY_TOKEN = ";"
    >>> _split_legacy_tokens(r"a;b;c;") != _split_legacy_tokens("a;b;c\\")
    True
    >>>

    Note that backslashes may be normalized
    >>> LEGACY_TOKEN = "\n"  # normal string behavior
    >>> _split_legacy_tokens(r"a\\\nb\nc")  # raw string input
    ['a\\\\nb\\nc']
    >>>

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
    ended_with_token: bool = False

    while index < len(value):
        if value[index] == "\\":
            ended_with_token = False  # reset
            escaped_token_start = index + 1

            if value.startswith(LEGACY_TOKEN, escaped_token_start):
                # preserve escaped token
                current.append(LEGACY_TOKEN)
                index += 1 + len(LEGACY_TOKEN)
            elif value.startswith("\\", escaped_token_start):
                # preserver escaped backslash
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
            ended_with_token = True  # set

        else:
            ended_with_token = False  # reset
            current.append(value[index])
            index += 1

    if not ended_with_token:
        parts.append("".join(current))

    return parts


def _serialize_input_str(value: Union[str, bytes, None]) -> Optional[str]:
    """Handle bytes and str uniformly."""
    if isinstance(value, (str, bytes)):
        if isinstance(value, bytes):
            # decode bytes as UTF-8
            try:
                value_str = value.decode()
            except UnicodeDecodeError:  # pragma: no cover
                value_str = cast(bytes, value).decode("utf-8")
            except UnicodeEncodeError:  # pragma: no cover
                value_str = str(
                    cast(str, value).encode("unicode_escape")  # type: ignore[arg-type]
                )
            except Exception:  # noqa: BLE001 -- blind catch-all
                # helper function should not raise an exception
                # fallback to dumb str(value) if decode fails
                value_str = str(value)
        else:
            value_str = value
        return value_str
    return None


def _parse_serialized(value: str) -> set[str]:
    """
    Parse a single string (already a str, not bytes) as a serialized value.

    - If LEGACY_TOKEN is present, split on unescaped LEGACY_TOKEN using
      _split_legacy_tokens, strip each token, and discard empty tokens.
      (This matches the original behavior where empty fields are discarded
      when the overall value contains LEGACY_TOKEN.)

    - If LEGACY_TOKEN is not present, return a single-element list with the
      stripped string (even if empty).

    Examples:
    >>> LEGACY_TOKEN = ";"
    >>> _parse_serialized("alpha;beta") == {'alpha', 'beta'}
    True
    >>> _parse_serialized("alpha;beta") == {'alpha;beta'}
    False
    >>> _parse_serialized("alpha;beta;") == {'alpha', 'beta'}
    True
    >>> _parse_serialized("  single  ") == {'single'}
    True
    >>> _parse_serialized("") == set()
    True
    >>>

    """
    if not value:
        return set()  # empty when falsey
    if LEGACY_TOKEN in value:
        # hint: can assume also is not None
        parts = _split_legacy_tokens(value)
        # strip and discard empties
        return {p.strip() for p in parts if p.strip() != ""}
    # no token: return single stripped value (preserve other string semantics)
    return {value.strip()} if value.strip() != "" else set()


def _normalize_as_set(
    value: Union[Iterable[object], str, bytes, None],
) -> set[str]:
    """
    Normalize a string, bytes, or iterable value into a flat set of strings.

    - None -> { } (e.g., empty)
    - str/bytes: treated as serialized values; unescaped LEGACY_TOKEN splits
      fields (backslash escapes LEGACY_TOKEN and backslash), if present. Empty fields
      are discarded.
    - Iterable: each element is normalized:
        - None elements are skipped
        - str/bytes elements are parsed as serialized values (split when token present)
        - other elements are converted with str(x).strip()

    >>> LEGACY_TOKEN = ";"
    >>> _normalize_as_set("alpha;beta") == {'alpha', 'beta'}
    True
    >>>

    >>> _normalize_as_set("alpha;beta;gamma") == {'alpha', 'beta', 'gamma'}
    True
    >>>

    >>> _normalize_as_set("alpha;beta;gamma;") == {'alpha', 'beta', 'gamma'}
    True
    >>>

    >>> _normalize_as_set("alpha\\;beta;gamma") == {'alpha;beta', 'gamma'}
    True
    >>>

    >>> _normalize_as_set(r"c:\\path;d") == {'c:\\\\path', 'd'}
    True
    >>>

    >>> _normalize_as_set(None) == set()
    True
    >>>

    >>> _normalize_as_set(["alpha", None, 42]) == {'alpha', '42'}
    True
    >>>

    TODO: handle this case:
    >>> _normalize_as_set(["alpha", "beta;gamma", None, 42]) == {'alpha', 'beta', 'gamma', '42'}
    True
    >>>

    TODO: handle this case:
    >>> _normalize_as_set(["alpha", "beta\\;gamma", None, 42]) == {'alpha', 'beta;gamma', '42'}
    True
    >>>

    """
    if value is None:
        return set()

    # Handle bytes and str uniformly
    if isinstance(value, (str, bytes)):
        _value_str = _serialize_input_str(value)
        return (
            _parse_serialized(_value_str)
            if isinstance(_value_str, str)
            else set()
        )

    # Otherwise expect an iterable. We'll flatten it.
    normalized: set[str] = set()
    try:
        for item in value:  # type: ignore[call-arg]
            if item is None:
                continue
            elif isinstance(item, (str, bytes)):
                item_str = _serialize_input_str(item)
                if (
                    item_str is None
                    or len(item_str.strip()) < 1
                    or item_str == LEGACY_TOKEN
                ):
                    continue
                _parsed_item = _parse_serialized(item_str)
                if _parsed_item:
                    normalized.update(_parsed_item)
                else:
                    continue
            elif isinstance(item, (list, set)):
                normalized.update(
                    _normalize_as_set([e for e in item if e is not None])
                )
            else:
                # Other types: convert to str and strip
                normalized.add(str(item).strip())
        return normalized
    except TypeError:
        # value was not iterable after all: best-effort to convert to str
        _best_guess = _serialize_input_str(str(value).strip())
        return {_best_guess} if _best_guess else set()


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
    >>> serialized = _serialize_to_semi_str({"beta", "alpha"})
    >>> serialized
    'alpha;beta'
    >>> _normalize_as_set(serialized) == {'alpha', 'beta'}
    True
    >>>

    >>> serialized_b = _serialize_to_semi_str({"alpha;beta", "gamma"})
    >>> _normalize_as_set(serialized_b) == {'alpha;beta', 'gamma'}
    True
    >>>

    >>> _serialize_to_semi_str(set()) == LEGACY_TOKEN
    True
    >>> _normalize_as_set(_serialize_to_semi_str(set())) == set()
    True
    >>>

    >>> _serialize_to_semi_str({" leading"}) == 'leading'
    True
    >>>

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


class FilePolicyError(ValueError):
    """Raised when a configuration cannot be normalized to a valid file policy."""


@dataclass(frozen=True)
class CategoryFilePolicy:
    enabled: bool = False
    contents: bool = False
    paths: bool = False

    @property
    def active(self) -> bool:
        return self.enabled and (self.contents or self.paths)

    def as_dict(self) -> dict[str, bool]:
        return {
            "enabled": self.enabled,
            "contents": self.contents,
            "paths": self.paths,
        }


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
    with_authors: bool = False
    with_maintainers: bool = False  # added in v6.0
    if "6.0" in __version__:
        with_notice_file: bool = False  # DEPRECIATED in v6.1
    with_notice_files: bool = False  # added in v6.0 (as boolean)
    with_other_files: bool = False  # added in v6.0 (as boolean)
    # removed no_license_path: bool = False  # DEPRECIATED in v6.1+
    with_license_paths: bool = False  # added in v6.0
    if "6.0" in __version__:
        no_file_paths: bool = False  # DEPRECIATED in v6.1+
    with_notice_paths: bool = False  # added in v6.0
    with_other_paths: bool = False  # added in v6.0
    # removed no_version: bool = False  # DEPRECIATED in v6.1+
    without_versions: bool = False
    filter_strings: bool = False
    partial_match: bool = False
    # string / optional values
    output_file: Optional[str] = None
    filter_code_page: Optional[str] = None
    # paths
    python: str = DEFAULT_PYTHON

    # new but un-implemented stuff
    # See https://github.com/raimon49/pip-licenses/issues/375
    with_licenses: bool = True  # added in v6.0
    with_others: bool = False  # added in v6.0
    with_notices: bool = False  # added in v6.0
    with_authors_files: bool = False  # added in v6.0
    with_authors_paths: bool = False  # added in v6.0
    with_attribution_files: bool = False  # added in v6.0
    with_attribution_paths: bool = False  # added in v6.0
    with_legacy_files: bool = "6.0" in __version__  # added in v6.0
    with_legacy_paths: bool = False  # added in v6.0
    # global-defaults
    global_files: Optional[bool] = None  # added in v6.0
    global_paths: Optional[bool] = None  # added in v6.0

    # sequence values
    fail_on: Optional[set] = field(default_factory=set)
    allow_only: Optional[set] = field(default_factory=set)
    ignore_packages: set[str] = field(default_factory=set)
    packages: set[str] = field(default_factory=set)
    warn_on: set[str] = field(default_factory=set)
    allow_packages: set[str] = field(default_factory=set)

    # computed values
    _resolved_file_policy: Optional[dict[str, CategoryFilePolicy]] = (
        None  # added in v6.0
    )

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
        if (self.fail_on is not None) and not isinstance(self.fail_on, set):
            self.fail_on = self._normalize_to_set(self.fail_on)
        if (self.allow_only is not None) and not isinstance(
            self.allow_only, set
        ):
            self.allow_only = self._normalize_to_set(self.allow_only)
        if not isinstance(self.allow_packages, set):
            self.allow_packages = self._normalize_to_set(self.allow_packages)
        if (self.warn_on is not None) and not isinstance(self.warn_on, set):
            self.warn_on = self._normalize_to_set(self.warn_on)

        self._resolved_file_policy: dict[str, CategoryFilePolicy] = {}
        self.validate()

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
           * no_license_path / without_license_paths ( --> not with_license_paths )
           * no_file_paths / without_file_paths ( --> not global_paths )
        """
        # only handle if given a string
        if not isinstance(name, str):
            raise AttributeError(name) from TypeError(name)  # noqa: TRY004 -- it's both

        _with_descriptions_map = [
            "with_description",
            "with_descriptions"
            if "6.1" in __version__
            else "with_description",
        ]

        _with_license_files_map = [
            "with_license_file",
            "with_license_files"
            if "6.1" in __version__
            else "with_license_file",
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

        # UNUSED
        # _dynamic_file_policy_map = [
        #     "_resolved_file_policy",
        #     "file_policy",
        # ]

        _with_license_cat_map = [
            "with_license",
            "with_licenses",
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
            _with_license_cat_map,
        ):
            if _pre_processed_name in _mapping:
                # Heuristic: warn if in any thru last alias (penultimate)
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
            "with_license_paths",
            "with_legacy_paths",
            "with_notice_paths",
            "with_other_paths",
            # "global_paths",  # optional bool
            "filter_strings",
            "partial_match",
            "without_versions",
        }
        inversions = {
            "with_license",  # True by default (rather inverse is False by default)
            # "with_notice",  # True by default (rather inverse is False by default)
            # "with_other",  # True by default (rather inverse is False by default)
            # "with_legacy",  # True by default (rather inverse is False by default)
            # "with_legacy_files",  # True by default (rather inverse is False by default)
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
        if _normalized_name in inversions:
            return True
        if _normalized_name in sets:
            return set()
        # Generic fallback
        return None

    def apply(self, **kwargs: Any) -> "Configuration":
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise AttributeError(f"Unknown configuration key: {key}")
            setattr(self, key, value)
        return self.validate()

    def validate(self) -> "Configuration":
        """
        Re-resolve file/path/text precedence until stable.

        This is intentionally idempotent and safe to call:
        - after each source is loaded
        - after merging config files
        - after CLI parsing
        - as a final canonicalization step
        """
        previous: Union[dict[str, CategoryFilePolicy], None] = None
        while True:
            resolved = self._resolve_file_policy()
            if previous is not None and resolved == previous:
                self._resolved_file_policy = resolved
                break
            previous = resolved
            self._apply_resolved_file_policy(resolved)
            self._resolved_file_policy = resolved

        return self

    @property
    def file_policy(self) -> dict[str, CategoryFilePolicy]:
        if not self._resolved_file_policy:
            self.validate()
            # See validate
            # self._resolved_file_policy will at-least be a dict[str, CategoryFilePolicy]
            # even if empty
        # Note: once again...
        # mypy (v1.19.1 for Python v3.9) is brain dead and forgets that optional != incompatible:
        # namely that {} (the empty dict) a still a subset of Union[dict, None]
        # (and while not all falsey is None; all None is falsey)...
        # e.g., mypy struggles with this concept:
        #
        # from typing import Union
        # >>> this_might_work: Union[dict, None] = None
        # >>> this_might_work
        # >>>
        # >>> this_wont
        # Traceback (most recent call last):
        #  File "<stdin>", line 1, in <module>
        # NameError: name 'this_wont' is not defined
        #
        # >>> this_will_work: dict = {}
        # >>> does_this_work: dict = this_might_work or {}
        # >>> does_this_work is not None
        # True
        # >>> does_this_work
        # {}
        #
        # so we need to ignore return-value here:
        return self._resolved_file_policy  # type: ignore[return-value]

    # GHI-375 -- handle edge-case of Configuration init
    @file_policy.setter
    def file_policy(
        self, value: Union[dict[str, CategoryFilePolicy], None]
    ) -> None:
        if not value or not isinstance(value, dict):
            return  # nothing to do
        # else
        self._apply_resolved_file_policy(value)

    @staticmethod
    def _read_tristate(obj: Any, *names: str) -> Union[bool, None]:  # noqa: ANN401 -- Dynamically typed at runtime
        for name in names:
            if not hasattr(obj, name):
                continue
            value = getattr(obj, name, None)
            if value is None:
                continue
            return bool(value)
        return None

    @staticmethod
    def _coalesce_bool(*values: Union[bool, None]) -> Union[bool, None]:
        for value in values:
            if value is not None:
                return value
        return None

    def _resolve_file_policy(self) -> dict[str, CategoryFilePolicy]:
        """
        Resolve per-category precedence:

        1. category-specific override wins over global defaults
        2. global defaults only apply when category-specific is unset
        3. explicit False wins over a broader True
        4. format-provided content support is enforced later; here we resolve the
           policy object, not the final format rendering gate
        """
        global_files = self._coalesce_bool(
            self._read_tristate(self, "global_files", "with_files"),
        )
        global_paths = self._coalesce_bool(
            self._read_tristate(self, "global_paths", "with_paths"),
        )

        category_map = {
            "license": (
                "with_license",
                "with_licenses",
                "with_license_files",
                "with_license_paths",
            ),
            "notice": (
                "with_notices",
                "with_notice_files",
                "with_notice_paths",
            ),
            "other": (
                "with_others",
                "with_other_files",
                "with_other_paths",
            ),
            "author": (
                "with_authors_files",
                "with_authors_paths",
            ),
            "attribution": (
                "with_attribution_files",
                "with_attribution_paths",
            ),
            "legacy": (
                "with_legacy_files",
                "with_legacy_paths",
            ),
        }

        resolved: dict[str, CategoryFilePolicy] = {}

        for category, names in category_map.items():
            category_enabled = self._coalesce_bool(
                self._read_tristate(self, names[0], names[1])
                if len(names) > 2
                else self._read_tristate(self, names[0]),
            )
            category_contents = self._coalesce_bool(
                self._read_tristate(self, names[-2]),
            )
            category_paths = self._coalesce_bool(
                self._read_tristate(self, names[-1]),
            )

            # legacy compatibility shims
            if category in ["license", "legacy"]:
                if self._read_tristate(self, "with_license_file") is not None:
                    legacy_file = self._read_tristate(
                        self, "with_license_file"
                    )
                    category_contents = self._coalesce_bool(
                        category_contents,
                        legacy_file,
                    )
                if self._read_tristate(self, "no_license_path") is not None:
                    legacy_path = self._read_tristate(self, "no_license_path")
                    category_paths = self._coalesce_bool(
                        category_paths,
                        not legacy_path if legacy_path is not None else None,
                    )
                if self._read_tristate(self, "no_file_paths") is not None:
                    legacy_global_path = self._read_tristate(
                        self, "no_file_paths"
                    )
                    category_paths = self._coalesce_bool(
                        category_paths,
                        (
                            not legacy_global_path
                            if legacy_global_path is not None
                            else None
                        ),
                    )

            if category == "notice":
                if self._read_tristate(self, "with_notice_file") is not None:
                    category_contents = self._coalesce_bool(
                        self._read_tristate(self, "with_notice_file") or None,
                        category_contents,
                    )
                if self._read_tristate(self, "with_notice_paths") is not None:
                    category_paths = self._coalesce_bool(
                        self._read_tristate(self, "with_notice_paths") or None,
                        category_paths,
                    )
                category_enabled = self._coalesce_bool(
                    category_enabled or None,  # allow force enable
                    category_contents or None,
                    category_paths,
                )

            # handle others
            if category in ["other", "author", "attribution", "legacy"]:
                category_enabled = self._coalesce_bool(
                    category_contents or None,
                    self._read_tristate(
                        self,
                        "with_others",
                        "with_other_files",
                    )
                    or None,
                    category_enabled or False,
                )

            enabled: bool = False
            contents: bool = False
            paths: bool = False

            # category enable is the master switch
            if category_enabled is not None:
                enabled = bool(category_enabled)
            elif global_files is True or global_paths is True:
                enabled = True

            if category_contents is not None:
                contents = bool(category_contents)
            elif global_files is True:
                contents = True

            if category_paths is not None:
                paths = bool(category_paths)
            elif global_paths is True:
                paths = True

            # Compatibility rule: content can imply paths when the category is
            # a legacy coupled file mode, unless the path setting was explicit.
            if (contents and category_paths is None) and (
                category in FORMAT_FLAG_OTHERS_GROUP
            ):
                paths = True

            # A disabled category cannot emit file content or file paths.
            if not enabled:
                enabled = False
                contents = False
                paths = False

            if enabled and not (contents or paths):
                # valid: category can be enabled without paths/text if the caller
                # intentionally wants a category-level toggle without output
                pass

            resolved[category] = CategoryFilePolicy(
                enabled=enabled,
                contents=contents,
                paths=paths,
            )

        return resolved

    def _apply_resolved_file_policy(
        self,
        resolved: dict[str, CategoryFilePolicy],
    ) -> None:
        """
        Synchronize the resolved canonical policy back into legacy fields for
        compatibility with older call sites and output code.
        """
        for category, policy in resolved.items():
            if category == "license":
                self.with_licenses = policy.enabled
                self.with_license_files = policy.contents
                self.with_license_paths = policy.paths
            elif category == "notice":
                self.with_notices = policy.enabled
                # WILL CHANGE BEHAVIOR IN v6.1
                if "v6.0." in __version__ or self.with_notice_file:
                    self.with_notice_file = policy.contents
                else:
                    self.with_notice_files = policy.contents
                self.with_notice_paths = policy.paths
            else:
                _current_state = self.with_others
                if category == "other":
                    self.with_others = (
                        policy.enabled
                    )  # allow with_others to be set to false
                    self.with_other_files = policy.contents
                    self.with_other_paths = policy.paths
                elif category == "author":
                    # self.with_authors = policy.enabled  # Does not come from file-policy
                    self.with_others = _current_state or policy.enabled
                    self.with_authors_files = policy.contents
                    self.with_authors_paths = policy.paths
                elif category == "attribution":
                    # self.with_maintainers = policy.enabled  # Does not come from file-policy
                    self.with_others = _current_state or policy.enabled
                    self.with_attribution_files = policy.contents
                    self.with_attribution_paths = policy.paths
                elif category == "legacy":
                    self.with_others = _current_state or policy.enabled
                    self.with_legacy_files = policy.contents
                    self.with_legacy_paths = policy.paths

        # Keep global defaults as a stable usable input layer, but category
        # policy remains authoritative.
        if getattr(self, "global_files", None) is None:
            self.global_files = self._coalesce_bool(
                self._read_tristate(self, "with_files"),
                self._read_tristate(self, "with_license_files"),
            )
        if getattr(self, "global_paths", None) is None:
            self.global_paths = self._coalesce_bool(
                self._read_tristate(self, "with_paths"),
                self._read_tristate(self, "with_license_paths"),
            )

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
    def without_license_paths(self) -> bool:
        return self.with_license_paths is False

    @without_license_paths.setter
    def without_license_paths(self, value: Union[bool, None]) -> None:
        self.with_license_paths = value is False

    @property
    def without_notice_paths(self) -> bool:
        return self.with_notice_paths is False

    @without_notice_paths.setter
    def without_notice_paths(self, value: Union[bool, None]) -> None:
        self.with_notice_paths = value is False

    @property
    def without_other_paths(self) -> bool:
        return self.with_other_paths is False

    @without_other_paths.setter
    def without_other_paths(self, value: Union[bool, None]) -> None:
        self.with_other_paths = value is False

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

        # DEPRECIATED in v6.0; use inverted global_paths instead.
        @property  # type: ignore[no-redef]
        def no_file_paths(self) -> bool:
            """DEPRECIATED in v6.1; use inverted global_paths instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use !global_paths instead.",
                stacklevel=2,
            )
            return not self.global_paths

        # DEPRECIATED in v6.0; use inverted global_paths instead.
        @no_file_paths.setter
        def no_file_paths(self, value: Union[bool, None]) -> None:
            """DEPRECIATED in v6.1; use inverted global_paths instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use !global_paths instead.",
                stacklevel=2,
            )
            if value is True:
                self.global_paths = False
            elif value is None:
                self.global_paths = None
            else:
                self.global_paths = True

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
            return self.with_license_files

        # DEPRECIATED in v6.0; use with_*s instead.
        @with_license_file.setter
        def with_license_file(self, value: Union[bool, None]) -> None:
            """DEPRECIATED in v6.1; use with_license_files instead."""
            warnings.warn(
                "DEPRECIATED in v6.1; use with_license_files instead.",
                stacklevel=2,
            )
            self.with_license_files = value is True

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

        # changed in v6.0
        @property  # type: ignore[no-redef]
        def no_license_path(self) -> bool:
            """DEPRECIATED in v6.0; use without_license_paths instead

            Previous to v6.0 there was no standardization of what are now:
            with/without prefixes.
            """
            return self.with_license_paths is False

        # changed in v6.0
        @no_license_path.setter
        def no_license_path(self, value: Union[bool, None]) -> None:
            """DEPRECIATED in v6.0; use without_license_paths instead.

            Previous to v6.0 there was no standardization of what are now:
            with/without prefixes.
            """
            if value:
                self.with_license_paths = False

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
