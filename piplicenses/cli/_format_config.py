# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et

# pip-licenses.cli._format_config
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


"""File format configuration model for granular control of file content/path output.

See [GHI-375](https://github.com/raimon49/pip-licenses/issues/375) for full design rationale.

PROTOTYPE; This component will move to a pip-licenses.config.??? in the future!
Do not rely on this component prior to v6.2;
see [GHI-375](https://github.com/raimon49/pip-licenses/issues/81) for integration details.
"""

from enum import (
    Flag,
    auto,
)
from typing import Union

from ._argparse_bridge import argparse  # the module
from ._format_nomenclature import reduce_to_config_form  # the function


class FileFormat(Flag):
    """Enumeration of files format modes."""

    # Individually
    SHOW_CONTENTS = auto()  # Include file contents
    SHOW_PATHS = auto()  # Include file paths
    # Combos
    SHOW_BOTH = SHOW_CONTENTS | SHOW_PATHS
    # Negation
    SHOW_NONE = 0  # semantically: ~SHOW_BOTH


class FileCategory(Flag):
    """Enumeration of all file discovery categories."""

    # Include recognized paths from core metadata Project-File
    METADATA = auto()  # 1 E.g., any files
    # Derive paths from core metadata License-File
    LICENSES = auto()  # 2 From core metadata License-File
    # Heuristic searches for other paths
    OTHERS = auto()  # 4 Catch-all for other extra files
    AUTHORS = auto()  # 8 Heuristic search for AUTHORS-like files
    ATTRIBUTION = auto()  # 16 Heuristic search for ATTRIBUTION-like files
    NOTICES = auto()  # 32 Heuristic search for NOTICE-like files
    LEGACY = (
        auto()
    )  # 64 Heuristic search for LICENSE/COPYING (not in metadata)
    # Combos
    ANY = (
        AUTHORS | ATTRIBUTION | NOTICES | LEGACY | OTHERS
    )  # 124 (127 - 1+2) E.g., any other paths


_FORMAT_CATEGORIES: list[FileCategory] = [
    FileCategory.ATTRIBUTION,
    FileCategory.AUTHORS,
    FileCategory.LEGACY,
    FileCategory.LICENSES,
    FileCategory.NOTICES,
    FileCategory.OTHERS,
]
"""Internal list of file-format-able categories.

Not part of the public API.
"""

_FORMAT_CATEGORIES_HINTS: dict[FileCategory, str] = {
    FileCategory.ATTRIBUTION: "attribution",
    FileCategory.AUTHORS: "authors",
    FileCategory.LEGACY: "legacy",
    FileCategory.LICENSES: "license",
    FileCategory.NOTICES: "notice",
    FileCategory.OTHERS: "other",
}
"""Internal list of _flags.FORMAT_FLAG_OTHERS_GROUP values mapped to format-able categories.

Not part of the public API.

    >>> from piplicenses.cli._flags import FORMAT_FLAG_OTHERS_GROUP
    >>> FORMAT_FLAG_OTHERS_GROUP is not None
    True
    >>> [bool(test_val in FORMAT_FLAG_OTHERS_GROUP) for test_val in _FORMAT_CATEGORIES_HINTS.items()]
    [True, True, True, True, True, True]
    >>>

"""


# validation rules:
# Ordered in order of operations from applies first to applies last.
# Rules are parsed for each change (e.g., initial, parsing, overrides, etc.) in rule-order,
# instead of flag-order, and rules have compound ordering effects (but rules are idempotent
# themselves). All flags are considered (un-ordered) for each rule,
# (e.g., --foo-flag --bar-flag is equivalent to --bar-flag --foo-flag) and can sometimes
# participate in multiple rules (like rule for effect, and rule for invalid total effect,
# eg. --summary)
#
# FileCategory:
#  flag --> either a requirement or a change, to be applied to the category (| for OR, = for set/replace, & for AND)
#
# ---
# Rules
#
# LICENSE:
#   --summary --> `= SHOW_NONE`
#   --without-files --> `& !SHOW_CONTENTS`
#   --without-paths --> `& !SHOW_PATHS`
#   --with-licenses --> `| SHOW_BOTH`
#   --with-license-file --> `= SHOW_BOTH`
#   --with-license-files --> `| SHOW_CONTENTS`
#   --with-license-paths --> `| SHOW_PATHS`
#   --with-files --> `| SHOW_CONTENTS`
#   --with-paths --> `| SHOW_PATHS`
#   --without-license-files --> `& !SHOW_CONTENTS`
#   --without-license-paths --> `& !SHOW_PATHS`
#   --without-licenses --> `& SHOW_NONE`
#   --summary --> require abort if LICENSE is not SHOW_NONE (conflicting licences-summary)
#   --with-license-files --> require abort if LICENSE is SHOW_NONE (conflicting with-without)
#   --with-license-paths --> require abort if LICENSE is SHOW_NONE (conflicting with-without)
#
#
# OTHERS:
#   --summary --> `= SHOW_NONE`
#   --without-files --> `& !SHOW_CONTENTS`
#   --without-paths --> `& !SHOW_PATHS`
#   --with-others --> `| SHOW_BOTH`
#   --with-other-files --> `| SHOW_CONTENTS`
#   --with-other-paths --> `| SHOW_PATHS`
#   --with-files --> `| SHOW_CONTENTS`
#   --with-paths --> `| SHOW_PATHS`
#   --without-other-files --> `& !SHOW_CONTENTS`
#   --without-other-paths --> `& !SHOW_PATHS`
#   --without-others --> `& SHOW_NONE`
#   --summary --> require abort if OTHERS is not SHOW_NONE (conflicting others-summary)
#   --with-others --> require abort if OTHERS is SHOW_NONE (conflicting with-without)
#
#
# ATTRIBUTION:
#   --summary --> `= SHOW_NONE`
#   --without-files --> `& !SHOW_CONTENTS`
#   --without-paths --> `& !SHOW_PATHS`
#   --without-others --> `& SHOW_NONE`
#   --with-others --> `| SHOW_BOTH`
#   --without-others --> require abort if ATTRIBUTION is NOT SHOW_NONE (conflicting with-without)
#   --with-attribution --> `| SHOW_BOTH`
#   --without-other-files --> `& !SHOW_CONTENTS`
#   --without-other-paths --> `& !SHOW_PATHS`
#   --with-attribution-files --> `| SHOW_CONTENTS`
#   --with-attribution-paths --> `| SHOW_PATHS`
#   --with-attribution -> require abort if ATTRIBUTION is SHOW_NONE (conflicting with-double-without)
#   --with-files --> `| SHOW_CONTENTS`
#   --with-paths --> `| SHOW_PATHS`
#   --without-attribution --> `& SHOW_NONE`
#   --with-attribution --> require abort if ATTRIBUTION is SHOW_NONE (conflicting with-without)
#   --with-attribution-files --> require abort if ATTRIBUTION is SHOW_NONE (conflicting with-without)
#   --without-attribution-files --> require abort if ATTRIBUTION is NOT any of (SHOW_NONE, SHOW_PATHS) (conflicting with-without)
#   --with-attribution-paths --> require abort if ATTRIBUTION is SHOW_NONE (conflicting with-without)
#   --without-attribution-paths --> require abort if ATTRIBUTION is NOT any of (SHOW_NONE, SHOW_CONTENTS) (conflicting with-without)
#   --summary --> require abort if ATTRIBUTION is not SHOW_NONE (conflicting others-summary)
#   --with-attribution-files --> (cli only) MAY abort if LICENCES is SHOW_NONE (conflicting authors-licences)
#   --with-attribution-paths --> (cli only) MAY abort if LICENCES is SHOW_NONE (conflicting authors-licences)
#
#
# AUTHORS:
#   --summary --> `= SHOW_NONE`
#   --without-files --> `& !SHOW_CONTENTS`
#   --without-paths --> `& !SHOW_PATHS`
#   --without-others --> `& SHOW_NONE`
#   --with-others --> `| SHOW_BOTH`
#   --without-others --> require abort if AUTHORS is NOT SHOW_NONE (conflicting with-without)
#   --without-other-files --> `& !SHOW_CONTENTS`
#   --without-other-paths --> `& !SHOW_PATHS`
#   --with-author-files --> `| SHOW_CONTENTS`
#   --with-author-paths --> `| SHOW_PATHS`
#   --with-files --> `| SHOW_CONTENTS`
#   --with-paths --> `| SHOW_PATHS`
#   --with-author-files --> require abort if AUTHORS is SHOW_NONE (conflicting with-without)
#   --without-author-files --> require abort if AUTHORS is NOT any of (SHOW_NONE, SHOW_PATHS) (conflicting with-without)
#   --with-author-paths --> require abort if AUTHORS is SHOW_NONE (conflicting with-without)
#   --without-attribution-paths --> require abort if AUTHORS is NOT any of (SHOW_NONE, SHOW_CONTENTS) (conflicting with-without)
#   --summary --> require abort if AUTHORS is not SHOW_NONE (conflicting authors-summary)
#   --with-author-files --> (cli only) MAY abort if LICENCES is SHOW_NONE (conflicting authors-licences)
#   --with-author-paths --> (cli only) MAY abort if LICENCES is SHOW_NONE (conflicting authors-licences)
#
#
# NOTICES:
#   --summary --> `= SHOW_NONE`
#   --without-files --> `& !SHOW_CONTENTS`
#   --without-paths --> `& !SHOW_PATHS`
#   --without-others --> `& SHOW_NONE`
#   --with-others --> `| SHOW_BOTH`
#   --without-others --> require abort if NOTICES is NOT SHOW_NONE (conflicting with-without)
#   --with-notices --> `| SHOW_BOTH`
#   --without-other-files --> `& !SHOW_CONTENTS`
#   --without-other-paths --> `& !SHOW_PATHS`
#   --with-notice-files --> `| SHOW_CONTENTS`
#   --with-notice-paths --> `| SHOW_PATHS`
#   --with-notices --> require abort if NOTICES is SHOW_NONE (conflicting with-double-without)
#   --with-files --> `| SHOW_CONTENTS`
#   --with-paths --> `| SHOW_PATHS`
#   --without-notices --> `& SHOW_NONE`
#   --with-notices --> require abort if NOTICES is SHOW_NONE (conflicting with-without)
#   --with-notice-files --> require abort if NOTICES is SHOW_NONE (conflicting with-without)
#   --without-notice-files --> require abort if NOTICES is NOT any of (SHOW_NONE, SHOW_PATHS) (conflicting with-without)
#   --with-notice-paths --> require abort if NOTICES is SHOW_NONE (conflicting with-without)
#   --without-notice-paths --> require abort if NOTICES is NOT any of (SHOW_NONE, SHOW_CONTENTS) (conflicting with-without)
#   --summary --> require abort if NOTICES is not SHOW_NONE (conflicting others-summary)
#   --with-notice-files --> (cli only) MAY abort if LICENCES is SHOW_NONE (conflicting notices-licences)
#   --with-notice-paths --> (cli only) MAY abort if LICENCES is SHOW_NONE (conflicting notices-licences)
#
#
# LEGACY:
#   --summary --> `= SHOW_NONE`
#   --without-files --> `& !SHOW_CONTENTS`
#   --without-paths --> `& !SHOW_PATHS`
#   --without-others --> `& SHOW_NONE`
#   --without-license-files --> `& SHOW_NONE`
#   --with-others --> `| SHOW_BOTH`
#   --with-license-files  --> `| SHOW_BOTH`
#   --without-others --> require abort if LEGACY is NOT SHOW_NONE (conflicting with-without)
#   --without-license-files --> require abort if LEGACY is NOT SHOW_NONE (conflicting with-without)
#   --with-attribution --> `| SHOW_BOTH`
#   --without-other-files --> `& !SHOW_CONTENTS`
#   --without-other-paths --> `& !SHOW_PATHS`
#   --with-legacy-files --> `| SHOW_CONTENTS`
#   --with-legacy-paths --> `| SHOW_PATHS`
#   --with-legacy --> require abort if LEGACY is SHOW_NONE (conflicting with-double-without)
#   --with-files --> `| SHOW_CONTENTS`
#   --with-paths --> `| SHOW_PATHS`
#   --without-legacy --> `& SHOW_NONE`
#   --with-legacy --> require abort if LEGACY is SHOW_NONE (conflicting with-without)
#   --with-legacy-files --> require abort if LEGACY is SHOW_NONE (conflicting with-without)
#   --without-legacy-files --> require abort if LEGACY is NOT any of (SHOW_NONE, SHOW_PATHS) (conflicting with-without)
#   --with-legacy-paths --> require abort if LEGACY is SHOW_NONE (conflicting with-without)
#   --without-legacy-paths --> require abort if LEGACY is NOT any of (SHOW_NONE, SHOW_CONTENTS) (conflicting with-without)
#   --summary --> require abort if LEGACY is not SHOW_NONE (conflicting others-summary)
#   --with-legacy-files --> (cli only) MAY abort if LICENCES is SHOW_NONE (conflicting legacy-licences)
#   --with-legacy-paths --> (cli only) MAY abort if LICENCES is SHOW_NONE (conflicting legacy-licences)
#
#
#  *:
#   --with-files --> require abort if all of (LICENCES, OTHERS, ATTRIBUTION, AUTHORS, NOTICES, LEGACY) are SHOW_NONE (invalid-state)
#   --with-paths --> require abort if all of (LICENCES, OTHERS, ATTRIBUTION, AUTHORS, NOTICES, LEGACY) are SHOW_NONE (invalid-state)
#


def _split_categories_into_list(value: FileCategory) -> list[FileCategory]:
    """Use to convert to a list of zero or more FileCategorys.

    Not part of the public API.
    """
    _value_categories: list[FileCategory] = []
    if value:
        _value_categories.extend(
            [
                _candidate
                for _candidate in _FORMAT_CATEGORIES
                if _candidate in value
            ]
        )
        # instead of just:
        # for _candidate in _FORMAT_CATEGORIES:
        #     if _candidate in value:
        #         _value_categories.append(_candidate)
    return _value_categories


def _category_enable_prefix(value: FileCategory) -> str:
    """Maps unique categories to corresponding prefix key hint.

    This is just the base stem (hint) of the flag, not the full prefix.

    see _FORMAT_CATEGORIES_HINTS
    see also _flags.FORMAT_FLAG_OTHERS_GROUP
    see also FileCategory

    Namely:
        * FileCategory.AUTHORS --> "authors"

        * FileCategory.LICENSES --> "license"
        * FileCategory.NOTICES --> "notice"
        * FileCategory.OTHERS -->  "other"
        * FileCategory.ATTRIBUTION --> "attribution"
        * FileCategory.LEGACY --> "legacy"

    Not part of the public API.
    """
    if not value:
        raise TypeError("Value must be non-empty")
    # otherwise try to map it
    if value in _FORMAT_CATEGORIES_HINTS:
        return _FORMAT_CATEGORIES_HINTS[value]
    else:
        raise ValueError("value must be a unique FileCategory.")


def _category_files_prefix(category: FileCategory) -> str:
    """Maps unique categories to corresponding prefix key hint.

    This is just the base stem (hint) of the flag, not the full prefix.

    see
    see also _flags.FORMAT_FLAG_OTHERS_GROUP
    see also FileCategory

    Namely:
        * FileCategory.AUTHORS --> "authors"
        * FileCategory.LICENSES --> "license"
        * FileCategory.NOTICES --> "notice"
        * FileCategory.OTHERS -->  "other"
        * FileCategory.ATTRIBUTION --> "attribution"
        * FileCategory.LEGACY --> "legacy"

    Not part of the public API.
    """
    if not category:
        raise ValueError("category must be non-empty")
    if not category.name:
        raise AttributeError(f"Unknown category or categories: {category!r}")
    _lowercase_category_name: str = category.name.lower()
    return (
        _lowercase_category_name.rstrip("s")
        if category != FileCategory.AUTHORS
        else _lowercase_category_name
    )


def _category_paths_prefix(category: FileCategory) -> str:
    """Internal helper.

    Not part of the public API.
    """
    return _category_files_prefix(category)


def _effective_bool(
    args: argparse.Namespace,
    dest: str,
    *,
    default: Union[bool, None] = None,
) -> Union[bool, None]:
    """Read a tri-state bool from a namespace attribute.

    In the v6 CLI, both --with-* and --without-* flags write to the same
    canonical dest, so the value is True / False / None.
    """
    value = getattr(args, dest, None)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return bool(value)


def _tri_state(args: argparse.Namespace, attr: str) -> Union[bool, None]:
    # deprecated
    return _effective_bool(args=args, dest=attr, default=None)


def _global_files_state(args: argparse.Namespace) -> Union[bool, None]:
    return _effective_bool(args, "with_files", default=None)


def _global_paths_state(args: argparse.Namespace) -> Union[bool, None]:
    return _effective_bool(args, "with_paths", default=None)


# uses
# _category_enable_prefix, _effective_bool _category_files_prefix
# _category_paths_prefix, FileCategory,
# _format_nomenclature.reduce_to_config_form
def _category_state(
    args: argparse.Namespace, category: FileCategory
) -> Union[bool, None]:
    prefix = _category_enable_prefix(category)
    return _effective_bool(
        args,
        reduce_to_config_form(f"with_{prefix}"),
        default=_effective_bool(
            args,
            reduce_to_config_form(
                f"with_{_category_files_prefix(category)}_files"
            ),
            default=_effective_bool(
                args,
                reduce_to_config_form(
                    f"with_{_category_paths_prefix(category)}_paths"
                ),
                default=None if "license" not in prefix else True,
            ),
        ),
    )


# uses
# _effective_bool _category_files_prefix
# FileCategory, _format_nomenclature.reduce_to_config_form
def _category_files_state(
    args: argparse.Namespace, category: FileCategory
) -> Union[bool, None]:
    prefix = _category_files_prefix(category)
    return _effective_bool(
        args=args,
        dest=reduce_to_config_form(f"with_{prefix}_files"),
        default=None,
    )


# uses
# _effective_bool _category_paths_prefix
# FileCategory, _format_nomenclature.reduce_to_config_form
def _category_paths_state(
    args: argparse.Namespace, category: FileCategory
) -> Union[bool, None]:
    prefix = _category_paths_prefix(category)
    return _effective_bool(
        args=args,
        dest=reduce_to_config_form(f"with_{prefix}_paths"),
        default=None,
    )


# uses
# _effective_bool
def _summary_active(args: argparse.Namespace) -> bool:
    """Check if summary mode is active or not.

    value is True => summary is active (return True)
    value is False => summary is disabled (return False)
    value is None => summary is not set (also return False)

    Not part of the public API.
    """
    # Note:  summary is not prefixed so no need to reduce via reduce_to_config_form
    return (
        bool(_effective_bool(args=args, dest="summary", default=None)) is True
    )


# uses
# _resolve_category_format, FileCategory, FileFormat
def resolve_file_format(
    args: argparse.Namespace,
    *,
    category: FileCategory = FileCategory.LEGACY,
) -> FileFormat:
    """Resolve a single effective FileFormat for a category given a namespace.

    This matches the actual v6 parser model: the parser stores a canonical
    boolean on the same dest for a pair of flags like:
      --with-license-files / --without-license-files
    """
    return _resolve_category_format(
        args,
        category=category,
        default=FileFormat.SHOW_NONE,
    )


# uses
# _category_state, _category_files_state, _category_paths_state,
# _summary_active,
# _global_files_state, _global_paths_state, FileCategory, FileFormat
def resolve_file_format_legacy(
    args: argparse.Namespace,
    *,
    category: FileCategory = FileCategory.LEGACY,
) -> FileFormat:
    """Resolve a single effective FileFormat for a category given a namespace.

    This matches the actual v6 parser model: the parser stores a canonical
    boolean on the same dest for a pair of flags like:
      --with-license-files / --without-license-files
    """
    # hint: reduce_to_config_form(prefix_hint)
    if category.name:  # e.g., only handle named categories
        formatted: FileFormat = FileFormat.SHOW_NONE
        file_show = False
        path_show = False
        category_state = _category_state(args, category)
        files_state = _category_files_state(args, category)
        paths_state = _category_paths_state(args, category)
        summary_state = _summary_active(args)

        # If summary is active, everything is off.
        if summary_state:
            formatted = FileFormat.SHOW_NONE
        # The category itself is the primary gate.
        if category_state is False:
            formatted = FileFormat.SHOW_NONE
            # TODO: actually still need to check conflicts before done
        if category_state is True:
            file_show = True
            path_show = True
        if files_state is not None:
            file_show = bool(files_state)  # T/F override narrow to files
        if paths_state is not None:
            path_show = bool(paths_state)  # T/F override narrow to paths
        # global flags still act as fallback/default to the whole category when
        # category-specific values are unspecified.
        if files_state is None and _global_files_state(args) is not None:
            file_show = bool(_global_files_state(args))
        if paths_state is None and _global_paths_state(args) is not None:
            path_show = bool(_global_paths_state(args))
        # now just need to canonicalize.
        if file_show and path_show:
            formatted = FileFormat.SHOW_BOTH
        elif file_show:
            formatted = FileFormat.SHOW_CONTENTS
        elif path_show:
            formatted = FileFormat.SHOW_PATHS
        else:
            formatted = FileFormat.SHOW_NONE
        # Now validate requirements
        _is_not_none_format = bool(formatted != FileFormat.SHOW_NONE)
        if summary_state and _is_not_none_format:
            raise AttributeError(
                "Conflicting flags for mode (summary): "
                "--with-* cannot be combined with --summary.",
                args,
            ) from ValueError(
                f"Ambiguous state: summary mode & {category!r} were both set!"
            )
        if category_state and _is_not_none_format:
            raise AttributeError(
                f"Conflicting flags for {category!r}: "
                f"--without-{_category_enable_prefix(category)} cannot be "
                "combined with "
                f"--with-{_category_files_prefix(category)}-files "
                f"or --with-{_category_paths_prefix(category)}-paths.",
            ) from ValueError(
                f"Ambiguous state: summary mode & {category!r} were both set!"
            )
        # TODO: need to check if formatted still makes sense based on rules
        return formatted
    else:
        raise ValueError(
            "Only supported (e.g., named) categories can be resolved! "
            f"{category!r} is NOT supported.",
        ) from AttributeError(f"{category!r} has no name!")


# uses
# _FORMAT_CATEGORIES, FileFormat, resolve_file_format
def resolve_file_formats(
    args: argparse.Namespace,
) -> dict[FileCategory, FileFormat]:
    """
    Convert argparse's tri-state booleans into FileFormat values.

    An unspecified setting inherits `default`.
    """
    formats: dict[FileCategory, FileFormat] = {
        category: resolve_file_format(
            args=args,
            category=category,
        )
        for category in _FORMAT_CATEGORIES
        if category.name
    }
    return formats


# uses
# _category_state, _category_files_state, _category_paths_state,
# _category_enable_prefix, _category_files_prefix, _FORMAT_CATEGORIES, _summary_active,
# _global_files_state, _global_paths_state, resolve_file_formats, FileFormat
def validate_file_format_namespace(
    parser: argparse.ArgumentParser,
    namespace: argparse.Namespace,
) -> None:
    """Validate the effective precedence rules under the real v6 parser shape.

    This is intentionally NOT a naive “if both booleans set then fail” check.
    It recognizes the valid GHI-375 cases:
      - category enabled + files disabled is valid
      - category enabled + paths disabled is valid
      - global files/paths can still be overridden by category-local false
      - category disabled + file/path enable is invalid
    """
    # summary short-circuits everything
    if _summary_active(namespace):
        return

    for category in _FORMAT_CATEGORIES:
        category_state = _category_state(namespace, category)
        files_state = _category_files_state(namespace, category)
        paths_state = _category_paths_state(namespace, category)

        # category disabled + a category-local path/files enable is invalid
        if category_state is False and (
            files_state is True or paths_state is True
        ):
            prefix_e = _category_enable_prefix(category)
            prefix = _category_files_prefix(category)
            # B.est G.uess S.uffix
            _bgs = "files" if files_state is True else "paths"
            _not_bgs = "paths" if files_state is True else "files"
            parser.error(
                f"Conflicting flags for {prefix}: "
                f"--without-{prefix_e} cannot be combined with "
                f"--with-{prefix}-files or --with-{prefix}-paths. "
                "Perhaps you wanted only one? "
                f"For just {_bgs}, try: --with-{prefix}-{_bgs} --without-{prefix}-{_not_bgs}. "
                f"Otherwise you might want to try: --with-{prefix_e} --without-{prefix}-{_not_bgs}."
            )

        # category enabled + category-local false is valid, not invalid.
        # It just narrows the output for that category.
        # For example:
        #   --with-license --without-license-files
        #   --with-license --without-license-paths
        # are legal.

    # Global enable with no categories active is invalid.
    if (
        _global_files_state(namespace) is True
        or _global_paths_state(namespace) is True
    ):
        resolved = resolve_file_formats(namespace)
        if not any(
            resolved[category] != FileFormat.SHOW_NONE
            for category in _FORMAT_CATEGORIES
        ):
            parser.error(
                "Invalid state: --with-files/--with-paths requires at least one "
                "active category."
            )


def _apply_effective_bit(
    *,
    current_files: bool,
    current_paths: bool,
    files_setting: Union[bool, None],
    paths_setting: Union[bool, None],
) -> tuple[bool, bool]:
    """Apply a tri-state override to current file/path booleans.

    None => no change
    True => enable
    False => disable

    Not part of the public API.
    """
    if files_setting is not None:
        current_files = bool(files_setting)
    if paths_setting is not None:
        current_paths = bool(paths_setting)
    return current_files, current_paths


def _apply_single_flag(
    current: FileFormat,
    *,
    value: Union[bool, None],
    show_files: bool,
    show_paths: bool,
) -> FileFormat:
    """Apply one boolean-ish flag to a FileFormat.

    value is True => enable the requested bit(s)
    value is False => disable the requested bit(s)
    value is None => no-op

    Not part of the public API.
    """
    if value is None:
        return current

    if value is True:
        if show_files:
            current |= FileFormat.SHOW_CONTENTS
        if show_paths:
            current |= FileFormat.SHOW_PATHS
        return current

    # value is False
    if show_files:
        current &= ~FileFormat.SHOW_CONTENTS
    if show_paths:
        current &= ~FileFormat.SHOW_PATHS
    return current


def _resolve_category_output_bits(
    args: argparse.Namespace,
    category: FileCategory,
) -> tuple[bool, bool]:
    """Return the effective show_files / show_paths for one category.

    This is the actual precedence logic for the v6 mutually-exclusive parser
    model. It is designed to allow:
      - with-category + without-files = valid
      - with-category + without-paths = valid
      - with-files + without-category-files = valid
    while rejecting:
      - without-category + with-category-files = invalid
      - without-category + with-category-paths = invalid
      - with-category + without-category + ... = invalid props are handled by
        the parser's mutually-exclusive group already, but we still guard here
        for safety
    """
    category_state = _category_state(args, category)
    files_state = _category_files_state(args, category)
    paths_state = _category_paths_state(args, category)

    global_files = _global_files_state(args)
    global_paths = _global_paths_state(args)

    # Default output off unless something explicitly enables it.
    current_files = False
    current_paths = False

    # 1) category state has highest priority for the category itself.
    #    If category is explicitly disabled, the category is off.
    if category_state is False:
        # explicit off for the category disables the category entirely.
        # file/path overrides are only meaningful when the category is active.
        # if caller passed an explicit file/path enable at the same time, reject
        # in validator stage.
        return False, False

    if category_state is True:
        # category on: default to both content + paths unless overridden
        current_files = True
        current_paths = True

    # 2) apply category-specific override flags.
    #    Explicit False means disable that aspect while keeping the category on.
    current_files, current_paths = _apply_effective_bit(
        current_files=current_files,
        current_paths=current_paths,
        files_setting=files_state,
        paths_setting=paths_state,
    )

    # 3) apply global toggles only when category-specific values are unspecified.
    if files_state is None and global_files is not None:
        current_files = bool(global_files)
    if paths_state is None and global_paths is not None:
        current_paths = bool(global_paths)

    return current_files, current_paths


# UNUSED ATM
def _resolve_category_format(
    args: argparse.Namespace,
    *,
    category: FileCategory,
    default: FileFormat = FileFormat.SHOW_NONE,
) -> FileFormat:
    """Apply the GHI #375 effects for one category in documented rule order.

    This resolves effects only. Cross-flag validity checks belong in the
    validation layer, where parser errors and Configuration errors can be
    reported appropriately.
    """
    if not category.name:
        raise ValueError(
            "Only named categories can be resolved: "
            f"{category!r} is not supported."
        )

    def _state(dest: str) -> Union[bool, None]:
        return _effective_bool(args, dest, default=None)

    def _update_bits(
        current: FileFormat,
        dest: str,
        *,
        on: FileFormat,
        off: FileFormat,
    ) -> FileFormat:
        """Apply a tri-state bit operation: None=no-op, True=OR, False=AND."""
        value = _state(dest)
        if value is True:
            return current | on
        if value is False:
            return current & off
        return current

    def _update_category_toggle(
        current: FileFormat,
        dest: str,
        *,
        on: FileFormat = FileFormat.SHOW_BOTH,
    ) -> FileFormat:
        """A category toggle enables its format, or disables the whole category."""
        value = _state(dest)
        if value is True:
            return current | on
        if value is False:
            return FileFormat.SHOW_NONE
        return current

    current = default
    # Every category starts with the summary reset. Do not return here:
    # later rules still apply, and validation checks whether the final state
    # conflicts with --summary.
    if _state("summary") is True:
        current = FileFormat.SHOW_NONE

    # Rule effects, in the order documented in GHI #375.
    if category == FileCategory.LICENSES:
        # --without-files / --without-paths
        current = _update_bits(
            current,
            "global_files",
            on=FileFormat.SHOW_NONE,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "global_paths",
            on=FileFormat.SHOW_NONE,
            off=~FileFormat.SHOW_PATHS,
        )

        # --with-licenses
        current = _update_category_toggle(current, "with_licenses")

        # Legacy singular flag: --with-license-file sets both bits.
        if _state("with_license_file") is True:
            current = FileFormat.SHOW_BOTH

        # --with-license-files / --with-license-paths
        current = _update_bits(
            current,
            "with_license_files",
            on=FileFormat.SHOW_CONTENTS,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "with_license_paths",
            on=FileFormat.SHOW_PATHS,
            off=~FileFormat.SHOW_PATHS,
        )

        # --with-files / --with-paths
        current = _update_bits(
            current,
            "global_files",
            on=FileFormat.SHOW_CONTENTS,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "global_paths",
            on=FileFormat.SHOW_PATHS,
            off=~FileFormat.SHOW_PATHS,
        )

        # --without-license-files / --without-license-paths
        # These are the same tri-state destinations as their --with forms.
        # Their False effect has already been applied above; the ordered
        # negative rules are represented here by the same idempotent AND.
        if _state("with_license_files") is False:
            current &= ~FileFormat.SHOW_CONTENTS
        if _state("with_license_paths") is False:
            current &= ~FileFormat.SHOW_PATHS

        # --without-licenses
        if _state("with_licenses") is False:
            current = FileFormat.SHOW_NONE

    elif category == FileCategory.OTHERS:
        # --without-files / --without-paths
        current = _update_bits(
            current,
            "global_files",
            on=FileFormat.SHOW_NONE,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "global_paths",
            on=FileFormat.SHOW_NONE,
            off=~FileFormat.SHOW_PATHS,
        )

        # --with-others; --with-other-files / --with-other-paths
        current = _update_category_toggle(current, "with_others")
        current = _update_bits(
            current,
            "with_other_files",
            on=FileFormat.SHOW_CONTENTS,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "with_other_paths",
            on=FileFormat.SHOW_PATHS,
            off=~FileFormat.SHOW_PATHS,
        )

        # --with-files / --with-paths
        current = _update_bits(
            current,
            "global_files",
            on=FileFormat.SHOW_CONTENTS,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "global_paths",
            on=FileFormat.SHOW_PATHS,
            off=~FileFormat.SHOW_PATHS,
        )

        # --without-other-files / --without-other-paths
        if _state("with_other_files") is False:
            current &= ~FileFormat.SHOW_CONTENTS
        if _state("with_other_paths") is False:
            current &= ~FileFormat.SHOW_PATHS

        # --without-others
        if _state("with_others") is False:
            current = FileFormat.SHOW_NONE

    elif category == FileCategory.ATTRIBUTION:
        # --without-files / --without-paths
        current = _update_bits(
            current,
            "global_files",
            on=FileFormat.SHOW_NONE,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "global_paths",
            on=FileFormat.SHOW_NONE,
            off=~FileFormat.SHOW_PATHS,
        )

        # --without-others / --with-others
        if _state("with_others") is False:
            current = FileFormat.SHOW_NONE
        elif _state("with_others") is True:
            current |= FileFormat.SHOW_BOTH

        # --with-attribution
        current = _update_category_toggle(current, "with_attribution")

        # --without-other-files / --without-other-paths
        if _state("global_files") is False:
            current &= ~FileFormat.SHOW_CONTENTS
        if _state("global_paths") is False:
            current &= ~FileFormat.SHOW_PATHS

        # --with-attribution-files / --with-attribution-paths
        current = _update_bits(
            current,
            "with_attribution_files",
            on=FileFormat.SHOW_CONTENTS,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "with_attribution_paths",
            on=FileFormat.SHOW_PATHS,
            off=~FileFormat.SHOW_PATHS,
        )

        # --with-files / --with-paths
        current = _update_bits(
            current,
            "global_files",
            on=FileFormat.SHOW_CONTENTS,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "global_paths",
            on=FileFormat.SHOW_PATHS,
            off=~FileFormat.SHOW_PATHS,
        )

        # --without-attribution
        if _state("with_attribution") is False:
            current = FileFormat.SHOW_NONE

    elif category == FileCategory.AUTHORS:
        # --without-files / --without-paths
        current = _update_bits(
            current,
            "global_files",
            on=FileFormat.SHOW_NONE,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "global_paths",
            on=FileFormat.SHOW_NONE,
            off=~FileFormat.SHOW_PATHS,
        )

        # --without-others / --with-others
        if _state("with_others") is False:
            current = FileFormat.SHOW_NONE
        elif _state("with_others") is True:
            current |= FileFormat.SHOW_BOTH

        # --without-other-files / --without-other-paths
        if _state("global_files") is False:
            current &= ~FileFormat.SHOW_CONTENTS
        if _state("global_paths") is False:
            current &= ~FileFormat.SHOW_PATHS

        # The current flag map uses "authors" in these destinations.
        current = _update_bits(
            current,
            "with_authors_files",
            on=FileFormat.SHOW_CONTENTS,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "with_authors_paths",
            on=FileFormat.SHOW_PATHS,
            off=~FileFormat.SHOW_PATHS,
        )

        # --with-files / --with-paths
        current = _update_bits(
            current,
            "global_files",
            on=FileFormat.SHOW_CONTENTS,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "global_paths",
            on=FileFormat.SHOW_PATHS,
            off=~FileFormat.SHOW_PATHS,
        )

    elif category == FileCategory.NOTICES:
        # --without-files / --without-paths
        current = _update_bits(
            current,
            "global_files",
            on=FileFormat.SHOW_NONE,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "global_paths",
            on=FileFormat.SHOW_NONE,
            off=~FileFormat.SHOW_PATHS,
        )

        # --without-others / --with-others
        if _state("with_others") is False:
            current = FileFormat.SHOW_NONE
        elif _state("with_others") is True:
            current |= FileFormat.SHOW_BOTH

        # --with-notices
        current = _update_category_toggle(current, "with_notices")

        # --without-other-files / --without-other-paths
        if _state("global_files") is False:
            current &= ~FileFormat.SHOW_CONTENTS
        if _state("global_paths") is False:
            current &= ~FileFormat.SHOW_PATHS

        # --with-notice-files / --with-notice-paths
        current = _update_bits(
            current,
            "with_notice_files",
            on=FileFormat.SHOW_CONTENTS,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "with_notice_paths",
            on=FileFormat.SHOW_PATHS,
            off=~FileFormat.SHOW_PATHS,
        )

        # --with-files / --with-paths
        current = _update_bits(
            current,
            "global_files",
            on=FileFormat.SHOW_CONTENTS,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "global_paths",
            on=FileFormat.SHOW_PATHS,
            off=~FileFormat.SHOW_PATHS,
        )

        # --without-notices
        if _state("with_notices") is False:
            current = FileFormat.SHOW_NONE

    elif category == FileCategory.LEGACY:
        # --without-files / --without-paths
        current = _update_bits(
            current,
            "global_files",
            on=FileFormat.SHOW_NONE,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "global_paths",
            on=FileFormat.SHOW_NONE,
            off=~FileFormat.SHOW_PATHS,
        )

        # --without-others / --without-license-files
        if _state("with_others") is False:
            current = FileFormat.SHOW_NONE
        if _state("with_license_files") is False:
            current = FileFormat.SHOW_NONE

        # --with-others / --with-license-files
        if _state("with_others") is True:
            current |= FileFormat.SHOW_BOTH
        if _state("with_license_files") is True:
            current |= FileFormat.SHOW_BOTH

        # --with-attribution
        if _state("with_attribution") is True:
            current |= FileFormat.SHOW_BOTH

        # --without-other-files / --without-other-paths
        if _state("global_files") is False:
            current &= ~FileFormat.SHOW_CONTENTS
        if _state("global_paths") is False:
            current &= ~FileFormat.SHOW_PATHS

        # --with-legacy-files / --with-legacy-paths
        current = _update_bits(
            current,
            "with_legacy_files",
            on=FileFormat.SHOW_CONTENTS,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "with_legacy_paths",
            on=FileFormat.SHOW_PATHS,
            off=~FileFormat.SHOW_PATHS,
        )

        # --with-files / --with-paths
        current = _update_bits(
            current,
            "global_files",
            on=FileFormat.SHOW_CONTENTS,
            off=~FileFormat.SHOW_CONTENTS,
        )
        current = _update_bits(
            current,
            "global_paths",
            on=FileFormat.SHOW_PATHS,
            off=~FileFormat.SHOW_PATHS,
        )

        # --without-legacy
        if _state("with_legacy") is False:
            current = FileFormat.SHOW_NONE

    else:
        raise ValueError(f"Unsupported file category: {category!r}")

    return current


__all__ = [
    "FileCategory",
    "FileFormat",
    "resolve_file_format",
    "resolve_file_formats",
    "validate_file_format_namespace",
]
