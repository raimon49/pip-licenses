# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et

# pip-licenses.cli._flags
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


"""Enumerated Flag Data.

To be documented?

See [GHI-360](https://github.com/raimon49/pip-licenses/issues/360).
"""

from typing import (
    Literal,  # after python 3.11 see LiteralString too
    TypedDict,
)

from ._format_nomenclature import (
    FORMAT_DISABLE_PREFIX,
    FORMAT_ENABLE_PREFIX,
    FORMAT_FILES_SUFFIX,
    FORMAT_OVERRIDE_FIELD,
    FORMAT_OVERRIDE_FIELD_OFF,
    FORMAT_OVERRIDE_FIELD_ON,
    FORMAT_PATHS_SUFFIX,
    FORMAT_TOGGLE_FIELD,
    FORMAT_TOGGLE_OFF,
    FORMAT_TOGGLE_ON,
    _normalize_to_config_form,
)

# Mark: Flag Nomenclature

# See https://github.com/raimon49/pip-licenses/issues/360
_ARG_PREFIX: Literal["-", "+", ""] = "-"  # e.g., a dash
"""Not part of the public API."""

# UNUSED
# See https://github.com/raimon49/pip-licenses/issues/360
_LONG_ARG_PREFIX: str = f"{_ARG_PREFIX}{_ARG_PREFIX}"  # e.g., two dashes
"""Not part of the public API."""

# UNUSED
# See https://github.com/raimon49/pip-licenses/issues/360
_scope_primitives: list[
    Literal["global", "fields", "contents", "files", "paths"]
] = [
    "global",
    "fields",
    FORMAT_FILES_SUFFIX,
    FORMAT_PATHS_SUFFIX,
]


# UNUSED
# See https://github.com/raimon49/pip-licenses/issues/360
# see typing.TypeIs
def _is_scope(value: object) -> bool:
    """Return whether value is exactly a compiled regular expression."""
    if isinstance(value, str):
        _delim = ", "
        if _delim in value:
            return all(tok in _scope_primitives for tok in value.split(_delim))
        else:
            return value in _scope_primitives
    return False


_FORMAT_FLAG_BASE_GROUP_S: set[str] = {
    "names",  # no flag; see --summary
    "versions",  # no flag; see --summary
}


_FORMAT_FLAG_BASE_GROUP_D: set[str] = {
    "licenses",
    "authors",
    "maintainers",
    "descriptions",
    "urls",
    "others",
}
"""flags that can toggle via enable/disable."""


# See https://github.com/raimon49/pip-licenses/issues/360
class ToggleFlagMap(TypedDict):
    enable: str
    disable: str
    initial: bool
    config_dest: str


FORMAT_DATA_FLAGS_MAP: dict[str, ToggleFlagMap] = {
    **{
        f"{_s_base}": {
            "enable": FORMAT_TOGGLE_ON.substitute(
                delimiter=f"{_ARG_PREFIX}", dest=f"{_s_base}"
            ),
            "disable": FORMAT_TOGGLE_OFF.substitute(
                delimiter=f"{_ARG_PREFIX}", dest=f"{_s_base}"
            ),
            "initial": True,
            "config_dest": _normalize_to_config_form(
                FORMAT_TOGGLE_FIELD.substitute(
                    delimiter="_", dest=f"{_s_base}"
                )
            ),
        }
        for _s_base in list(_FORMAT_FLAG_BASE_GROUP_S)
    },
    **{
        f"{_d_base}": {
            "enable": FORMAT_TOGGLE_ON.substitute(
                delimiter=f"{_ARG_PREFIX}", dest=f"{_d_base}"
            ),
            "disable": FORMAT_TOGGLE_OFF.substitute(
                delimiter=f"{_ARG_PREFIX}", dest=f"{_d_base}"
            ),
            "initial": _d_base == "licenses",
            "config_dest": _normalize_to_config_form(
                FORMAT_TOGGLE_FIELD.substitute(
                    delimiter="_", dest=f"{_d_base}"
                )
            ),
        }
        for _d_base in list(_FORMAT_FLAG_BASE_GROUP_D)
    },
    "notices": {
        "enable": FORMAT_TOGGLE_ON.substitute(
            delimiter=f"{_ARG_PREFIX}", dest="notices"
        ),
        "disable": FORMAT_TOGGLE_OFF.substitute(
            delimiter=f"{_ARG_PREFIX}", dest="notices"
        ),
        "initial": False,
        "config_dest": _normalize_to_config_form(
            FORMAT_TOGGLE_FIELD.substitute(delimiter="_", dest="notices")
        ),
    },
}

# import ._argparse_bridge._add_toggle_argument_group

_FORMAT_FLAG_BASE_GROUP_F: set[str] = {
    "attribution",
    "authors",
    "legacy",
    "license",
    "notice",
    "other",
}
"""Other flags that can toggle via enable/disable for files and/or paths."""


FORMAT_FILES_FLAGS_MAP: dict[str, ToggleFlagMap] = {
    **{
        f"{_f_base}-{FORMAT_FILES_SUFFIX}": {
            "enable": FORMAT_OVERRIDE_FIELD_ON.substitute(
                delimiter=_ARG_PREFIX,
                dest=_f_base,
                suffix=FORMAT_FILES_SUFFIX,
            ),
            "disable": FORMAT_OVERRIDE_FIELD_OFF.substitute(
                delimiter=_ARG_PREFIX,
                dest=_f_base,
                suffix=FORMAT_FILES_SUFFIX,
            ),
            "initial": False,
            "config_dest": _normalize_to_config_form(
                FORMAT_OVERRIDE_FIELD.substitute(
                    delimiter=_ARG_PREFIX,
                    dest=_f_base,
                    suffix=FORMAT_FILES_SUFFIX,
                ),
            ),
        }
        for _f_base in list(_FORMAT_FLAG_BASE_GROUP_F)
    },
    f"{FORMAT_FILES_SUFFIX}": {
        "enable": f"{FORMAT_ENABLE_PREFIX}-{FORMAT_FILES_SUFFIX}",
        "disable": f"{FORMAT_DISABLE_PREFIX}-{FORMAT_FILES_SUFFIX}",
        "initial": False,
        "config_dest": _normalize_to_config_form(
            f"global_{FORMAT_FILES_SUFFIX}"
        ),
    },
}


FORMAT_PATHS_FLAGS_MAP: dict[str, ToggleFlagMap] = {
    **{
        f"{_p_base}-{FORMAT_PATHS_SUFFIX}": {
            "enable": FORMAT_OVERRIDE_FIELD_ON.substitute(
                delimiter=_ARG_PREFIX,
                dest=_p_base,
                suffix=FORMAT_PATHS_SUFFIX,
            ),
            "disable": FORMAT_OVERRIDE_FIELD_OFF.substitute(
                delimiter=_ARG_PREFIX,
                dest=_p_base,
                suffix=FORMAT_PATHS_SUFFIX,
            ),
            "initial": False,
            "config_dest": _normalize_to_config_form(
                FORMAT_OVERRIDE_FIELD.substitute(
                    delimiter=_ARG_PREFIX,
                    dest=_p_base,
                    suffix=FORMAT_PATHS_SUFFIX,
                ),
            ),
        }
        for _p_base in list(_FORMAT_FLAG_BASE_GROUP_F)
    },
    f"{FORMAT_PATHS_SUFFIX}": {
        "enable": f"{FORMAT_ENABLE_PREFIX}-{FORMAT_PATHS_SUFFIX}",
        "disable": f"{FORMAT_DISABLE_PREFIX}-{FORMAT_PATHS_SUFFIX}",
        "initial": False,
        "config_dest": _normalize_to_config_form(
            f"global_{FORMAT_PATHS_SUFFIX}"
        ),
    },
}


FORMAT_TOGGLE_FLAGS_MAP: dict[str, ToggleFlagMap] = {
    **FORMAT_DATA_FLAGS_MAP,
    **FORMAT_FILES_FLAGS_MAP,
    **FORMAT_PATHS_FLAGS_MAP,
}


FORMAT_FLAG_OTHERS_GROUP: set[str] = {
    "attribution",
    "authors",
    "legacy",
    "license",
    "notice",
    "other",
}
"""Other flags placeholder. NOT PART OF ANY API."""


__all__ = [
    """FORMAT_FLAG_OTHERS_GROUP""",
    """FORMAT_TOGGLE_FLAGS_MAP""",
    """_ARG_PREFIX""",
    """_LONG_ARG_PREFIX""",
    """ToggleFlagMap""",  # Used by ._argparse_bridge
]
