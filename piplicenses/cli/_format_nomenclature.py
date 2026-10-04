# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et

# pip-licenses.cli._format_nomenclature
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


"""Enumerated nomenclature.

Namely:
    * Prefixes
        * "with" (e.g., enable/include)
        * "without" (e.g., disable/suppress)
    * Suffixes
        * "files" (e.g., file contents)
        * "paths" (e.g., file contents)
    * Templates
        * toggles (e.g., plain on/off toggles)
            * fields (e.g., plain/parent category form)
            * toggle-flags (e.g., on/off toggle flag form)
        * overrides
            * files-fields (e.g., files/specific category form)
            * files-flags (e.g., files/specific on/off override toggle flag form)
            * paths-fields (e.g., paths/specific category form)
            * paths-flags (e.g., paths/specific on/off override toggle flag form)

All Templates expect a `delimiter` (e.g., "-" (dash) or "_" (underscore))
and a base `dest` (e.g., "")

See [GHI-375](https://github.com/raimon49/pip-licenses/issues/375).

[GHI-81](https://github.com/raimon49/pip-licenses/issues/81):
Not part of the _public_ API. Subject to sudden changes, or removal.
"""

# These may be used to add localizations eventually.

from string import Template
from typing import Literal

# See https://github.com/raimon49/pip-licenses/issues/360
FORMAT_ENABLE_PREFIX: Literal["show", "include", "with", "enable"] = "with"
"""This prefix is used for names used in enabling format fields of the config.

Not part of the public API. Subject to sudden changes, or removal.
"""

FORMAT_DISABLE_PREFIX: str = f"{FORMAT_ENABLE_PREFIX}out"
"""This prefix is used for names used in omitting format fields of the config.

Not part of the public API. Subject to sudden changes, or removal.
"""

FORMAT_FILES_SUFFIX: Literal["contents", "files"] = "files"
"""This suffix is used for names used in overriding files-format fields of the config.

Not part of the public API. Subject to sudden changes, or removal.
"""

FORMAT_PATHS_SUFFIX: Literal["paths"] = "paths"
"""This suffix is used for names used in overriding file-paths-format fields flags of the config.

Not part of the public API. Subject to sudden changes, or removal.
"""

DELIMITER: Literal["delimiter"] = "delimiter"
"""This is the VAR name for delimiters in format templates.

Not part of the public API. Subject to sudden changes, or removal.
"""

DEST: Literal["dest"] = "dest"
"""This is the VAR name for destination bases in format templates.

Not part of the public API. Subject to sudden changes, or removal.
"""

SUFFIX: Literal["suffix"] = "suffix"
"""This is the VAR name for suffix in format override templates.

Not part of the public API. Subject to sudden changes, or removal.
"""

FORMAT_TOGGLE_FIELD: Template = Template(
    f"{FORMAT_ENABLE_PREFIX}$delimiter$dest"
)
"""This template is for generating flag and config names from a base dest.

Not part of the public API. Subject to sudden changes, or removal.
"""

FORMAT_TOGGLE_ON: Template = Template(
    f"$delimiter${{delimiter}}{FORMAT_ENABLE_PREFIX}$delimiter$dest"
)
"""This template is for generating enable flag names from a base dest.

Not part of the public API. Subject to sudden changes, or removal.
"""

FORMAT_TOGGLE_OFF: Template = Template(
    f"$delimiter${{delimiter}}{FORMAT_DISABLE_PREFIX}$delimiter$dest"
)
"""This template is for generating suppression flag names from a base dest.

Not part of the public API. Subject to sudden changes, or removal.
"""

FORMAT_OVERRIDE_FIELD: Template = Template(
    f"{FORMAT_ENABLE_PREFIX}$delimiter$dest$delimiter$suffix"
)
"""This template is for generating flag and config names for file overrides from a base dest.

Not part of the public API. Subject to sudden changes, or removal.
"""

FORMAT_OVERRIDE_FIELD_ON: Template = Template(
    f"$delimiter${{delimiter}}{FORMAT_ENABLE_PREFIX}$delimiter$dest$delimiter$suffix"
)
"""This template is for generating enable flag names for overrides from a base dest.

Not part of the public API. Subject to sudden changes, or removal.
"""

FORMAT_OVERRIDE_FIELD_OFF: Template = Template(
    f"$delimiter${{delimiter}}{FORMAT_DISABLE_PREFIX}$delimiter$dest$delimiter$suffix"
)
"""This template is for generating suppression flag names for overrides from a base dest.

Not part of the public API. Subject to sudden changes, or removal.
"""


def _require_nonempty_string(value: object, context: str) -> str:
    """Validate the input is a non-empty string before returning the value, or raise an error.

    Developer note: Subclasses of str are also invalid if they behave
    as false-y. (e.g., length is just the default).
    """
    _context: str = context or "value"
    if not isinstance(value, str):
        raise TypeError(
            f"{_context} must be a string, got {type(value).__name__}"
        ) from None
    if not value:
        # See https://docs.python.org/3/library/stdtypes.html#truth-value-testing
        if len(value) > 0:
            # handle subclasses that are false but non-empty
            raise ValueError(f"{_context} must not be false-y") from None
        # otherwise treat false as empty
        raise ValueError(f"{_context} must not be empty") from None
    return value


def _normalize_to_config_form(hint: str) -> str:
    """Normalizes the input hint into a normalized config key form.

    In general transcode dashes to underscore and drop all case to lower, then strip
    leading and trailing spaces and underscores.
    """
    # validate first
    _hint = _require_nonempty_string(
        value=hint,
        context="Can not normalize value to a config key;",
    )
    # else can try to normalize (best-effort for now)
    # if we pull in re (via an import re), then we could consider:
    # re.sub(r"[ _.\-\t\n\r]+", "_", _hint)
    _to_be_stripped_chars: str = " _.-\t\n\r"
    return (
        _hint.replace("-", "_")
        .lower()
        .lstrip(_to_be_stripped_chars)
        .strip(_to_be_stripped_chars)
    )


def _generate_all_config_forms(hint: str) -> list[str]:
    """Attempt to heuristically generate a list of each config key form for the given hint.

    In general will return a form of each FIELD template based on:
    `template.substitute({delimiter="_", dest=hint}) for template in` _all field templates_.

    Caution: Not all returned values are guaranteed to be actual implemented config keys.

    Not part of the public API. Subject to sudden changes, or removal.
    """
    # validate first
    _mapping_base: dict = {
        DELIMITER: "_",
        DEST: _normalize_to_config_form(hint),
    }
    # and map out
    _mapping_files_override: dict = {SUFFIX: FORMAT_FILES_SUFFIX}
    _mapping_files_override.update(_mapping_base.copy())
    _mapping_paths_override: dict = {SUFFIX: FORMAT_PATHS_SUFFIX}
    _mapping_paths_override.update(_mapping_base.copy())
    _mappings: list[tuple[Template, dict]] = [
        (FORMAT_TOGGLE_FIELD, _mapping_base),
        (FORMAT_OVERRIDE_FIELD, _mapping_files_override),
        (FORMAT_OVERRIDE_FIELD, _mapping_paths_override),
    ]
    return [template.substitute(mapping) for template, mapping in _mappings]


def _generate_only_config_form(hint: str) -> list[str]:
    """Attempt to heuristically generate a list of one config key form for the given hint.

    In general is the same as FORMAT_TOGGLE_FIELD template based on:
    `[FORMAT_TOGGLE_FIELD.substitute({delimiter="_", dest=hint})]`.

    Caution: Not all returned values are guaranteed to be actual implemented config keys.

    Not part of the public API. Subject to sudden changes, or removal.
    """
    # validate and map first
    _mappings: dict = {DELIMITER: "_", DEST: _normalize_to_config_form(hint)}
    return [
        FORMAT_TOGGLE_FIELD.substitute(_mappings),
    ]


def reduce_to_config_form(base_hint: str) -> str:
    """Attempt to heuristically generate a config key form for the given hint.

    In general is the same as FORMAT_TOGGLE_FIELD template based on:
    `[FORMAT_TOGGLE_FIELD.substitute({delimiter="_", dest=hint})]`.

    Caution: returned values are NOT guaranteed to be actual implemented config keys;
    rather values returned are merely guaranteed to be in a canonical normalized format.

    """
    # validate (via normalize) first
    _hint = _normalize_to_config_form(base_hint)
    # check if prefix is anywhere in normalized string
    if FORMAT_ENABLE_PREFIX in _hint or FORMAT_DISABLE_PREFIX in _hint:
        # heuristically consider the presence of these sub-strings to be formatted
        # generalize to canonical form (e.g., always enable form) and return
        return _hint.replace(FORMAT_DISABLE_PREFIX, FORMAT_ENABLE_PREFIX, 1)
    # otherwise consider prefix is missing and needs a template
    # then map next
    # morally should be dict[Literal, str]
    _mappings: dict = {DELIMITER: "_", DEST: _hint}
    # then transform and re-normalize
    return _normalize_to_config_form(
        FORMAT_TOGGLE_FIELD.substitute(_mappings),
    )


# See https://github.com/raimon49/pip-licenses/issues/360
# See https://github.com/raimon49/pip-licenses/issues/359
# placeholder for transient config file Format mapping types


def generate_config_mapping(hint: str) -> dict[str, str]:
    """Attempt to heuristically generate a list of each config key form for the given hint.

    In general will return a form of each FIELD template based on:
    `template.substitute({delimiter="_", dest=hint}) for template in` _all field templates_.

    Caution: Not all returned values are guaranteed to be actual implemented config keys.

    Not part of the public API. Subject to sudden changes, or removal.
    """
    # validate and map first
    _mappings: dict = {DELIMITER: "_", DEST: _normalize_to_config_form(hint)}
    return {
        "field": FORMAT_TOGGLE_FIELD.substitute(_mappings),
        FORMAT_FILES_SUFFIX: Template(
            FORMAT_OVERRIDE_FIELD.safe_substitute(_mappings)
        ).substitute(
            suffix=FORMAT_FILES_SUFFIX,
        ),
        FORMAT_PATHS_SUFFIX: Template(
            FORMAT_OVERRIDE_FIELD.safe_substitute(_mappings)
        ).substitute(
            suffix=FORMAT_PATHS_SUFFIX,
        ),
    }


def _generate_expected_config_forms(
    hint: str, has_overrides: bool
) -> list[str]:
    """Attempt to heuristically generate a list of each config key form for the given hint.

    In general will return a form of each FIELD template based on:
    `template.substitute({delimiter="_", dest=hint}) for template in` _expected field templates_.

    Caution: Not all returned values are guaranteed to be actual implemented config keys.

    Not part of the public API. Subject to sudden changes, or removal.
    """
    if has_overrides is True:
        return _generate_all_config_forms(hint)
    else:
        return _generate_only_config_form(hint)


def _generate_toggle_flag_forms(hint: str) -> list[str]:
    """Enumerates the input hint into a normalized list of each ON/OFF flag form.

    In general will return a form of each ON/OFF template based on:
    `template.substitute({delimiter="-", dest=hint}) for template in` _ON/OFF flag templates_.
    """
    # validate first
    _hint = _require_nonempty_string(
        value=hint,
        context="Can not enumerate value in flag forms;",
    )
    # else can try to normalize
    _mappings: dict = {DELIMITER: "-", DEST: hint}
    return [
        template.substitute(_mappings)
        for template in [
            FORMAT_TOGGLE_ON,
            FORMAT_TOGGLE_OFF,
        ]
    ]


def _generate_all_flag_forms(hint: str) -> list[str]:
    """Enumerates the input hint into a normalized list of each flag form.

    In general will return a form of each ON/OFF template based on:
    `template.substitute({delimiter="-", dest=hint}) for template in` _all flag templates_.
    """
    # validate first
    _hint = _require_nonempty_string(
        value=hint, context="Can not enumerate value in flag forms;"
    )
    # else can try to normalize
    _mappings: dict = {DELIMITER: "-", DEST: hint}
    return [
        *_generate_toggle_flag_forms(hint),
        *[
            Template(template.safe_substitute(_mappings)).substitute(
                suffix=FORMAT_FILES_SUFFIX,
            )
            for template in [
                FORMAT_OVERRIDE_FIELD_ON,
                FORMAT_OVERRIDE_FIELD_OFF,
            ]
        ],
        *[
            Template(template.safe_substitute(_mappings)).substitute(
                suffix=FORMAT_PATHS_SUFFIX,
            )
            for template in [
                FORMAT_OVERRIDE_FIELD_ON,
                FORMAT_OVERRIDE_FIELD_OFF,
            ]
        ],
    ]


def _generate_expected_flag_forms(hint: str, has_overrides: bool) -> list[str]:
    """Attempt to heuristically generate a list of each config key form for the given hint.

    In general will return a form of each FIELD template based on:
    `template.substitute({delimiter="_", dest=hint}) for template in` _expected field templates_.

    Caution: Not all returned values are guaranteed to be actual implemented flags.

    Not part of the public API. Subject to sudden changes, or removal.
    """
    if has_overrides is True:
        return _generate_all_flag_forms(hint)
    else:
        return _generate_toggle_flag_forms(hint)


__all__ = [
    # Nomenclature
    """FORMAT_DISABLE_PREFIX""",
    """FORMAT_ENABLE_PREFIX""",
    """FORMAT_FILES_SUFFIX""",
    """FORMAT_OVERRIDE_FIELD""",
    """FORMAT_OVERRIDE_FIELD_OFF""",
    """FORMAT_OVERRIDE_FIELD_ON""",
    """FORMAT_PATHS_SUFFIX""",
    """FORMAT_TOGGLE_FIELD""",
    """FORMAT_TOGGLE_OFF""",
    """FORMAT_TOGGLE_ON""",
    # Helper Functions
    """_generate_all_flag_forms""",
    """_normalize_to_config_form""",
    # Util Functions
    """generate_config_mapping""",
    """reduce_to_config_form""",
]
