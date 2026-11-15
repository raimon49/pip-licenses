# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et

# pip-licenses.cli._mutually_exclusive_toggle
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

"""
This is the v6-compatible action layer for the parser.

It assumes the CLI defines paired flags on the same canonical dest, e.g.
  --with-license-files
  --without-license-files
both mutate args.with_license_files = True/False.
"""

# See https://github.com/raimon49/pip-licenses/issues/360
from typing import Union

from ._argparse_bridge import argparse
from ._flags import (
    FORMAT_TOGGLE_FLAGS_MAP,
    ToggleFlagMap,
)
from ._format_config import validate_file_format_namespace

# Example usage:
#
# parser = argparse.ArgumentParser()
# add_mutually_exclusive_flag_pair(
#     parser,
#     enable_flag="--with-license",
#     disable_flag="--without-license",
#     dest="with_license",
#     help_text="include license metadata",
#     default=None,
# )
#
# add_mutually_exclusive_flag_pair(
#     parser,
#     enable_flag="--with-license-files",
#     disable_flag="--without-license-files",
#     dest="with_license_files",
#     help_text="include license file contents",
#     default=None,
# )
#
# add_mutually_exclusive_flag_pair(
#     parser,
#     enable_flag="--with-license-paths",
#     disable_flag="--without-license-paths",
#     dest="with_license_paths",
#     help_text="include license file paths",
#     default=None,
# )


# See https://github.com/raimon49/pip-licenses/issues/360
_ARGUMENT_GROUP_TYPE = type(
    argparse.ArgumentParser().add_argument_group("Group Type")
)
"""Not part of the public API."""


# See https://github.com/raimon49/pip-licenses/issues/360
# morally this is a special boolean of typing.TypeIs[re.Pattern] but that requires python3.13+
# see typing.TypeIs
def _is_argument_group(value: object) -> bool:
    """Return whether value is exactly an argparser argument group."""
    return type(value) is _ARGUMENT_GROUP_TYPE


# See https://github.com/raimon49/pip-licenses/issues/360
# morally this is a special boolean of typing.TypeIs[re.Pattern] but that requires python3.13+
# see typing.TypeIs
def _is_valid_argument_container(value: object) -> bool:
    """Return whether value will accept add_mutually_exclusive_group()."""
    if hasattr(value, "add_mutually_exclusive_group"):
        return True  # simple case
    if not isinstance(
        value,
        (argparse.ArgumentParser, argparse._ArgumentGroup),
    ):
        raise TypeError(
            f"parser is of the wrong type: {type(value)}"
        ) from None
    else:
        return True


class StoreMutuallyExclusiveToggleAction(argparse.Action):
    """Action for a v6 paired toggle like:
        --with-license-files / --without-license-files

    Both flags set the same destination, but with different bool values.
    """

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: object,
        option_string: Union[str, None] = None,
    ) -> None:
        # self.const is already the intended value (True or False)
        setattr(namespace, self.dest, self.const)
        validate_file_format_namespace(parser, namespace)


def add_mutually_exclusive_flag_pair(
    parser: Union[argparse.ArgumentParser, argparse._ArgumentGroup],
    *,
    enable_flag: str,
    disable_flag: str,
    dest: str,
    help_text: str,
    default: Union[bool, None] = None,
) -> Union[argparse.ArgumentParser, argparse._ArgumentGroup]:
    """Add a single v6 pair to a mutually exclusive group.

    Not part of the public API.
    """
    if not _is_valid_argument_container(parser):
        raise ValueError(f"Invalid parser: {parser!r}.") from None
    some_mutually_exclusive_group = parser.add_mutually_exclusive_group()
    try:
        some_mutually_exclusive_group.add_argument(
            enable_flag,
            action=StoreMutuallyExclusiveToggleAction,
            nargs=0,
            const=True,
            default=default,
            help=f"{help_text} (enable)",
            dest=dest,
        )
        some_mutually_exclusive_group.add_argument(
            disable_flag,
            action=StoreMutuallyExclusiveToggleAction,
            nargs=0,
            const=False,
            default=default,
            help=f"{help_text} (disable)",
            dest=dest,
        )
    except TypeError as _type_err:
        raise ValueError(
            f"Failed to add pair of arguments for {enable_flag}/{disable_flag}."
        ) from _type_err
    else:
        return parser


def _add_toggle_argument_group(
    parser_in: Union[argparse.ArgumentParser, argparse._ArgumentGroup],
    arg_key: str,
    toggle_map: ToggleFlagMap,
) -> Union[argparse.ArgumentParser, argparse._ArgumentGroup]:
    """Not part of the public API."""
    try:
        parser_in = add_mutually_exclusive_flag_pair(
            parser=parser_in,
            enable_flag=toggle_map["enable"],
            disable_flag=toggle_map["disable"],
            dest=toggle_map["config_dest"],
            help_text=f"Toggles output of package {arg_key}.",
            default=toggle_map["initial"],
        )
    except TypeError as _type_err:
        raise ValueError(
            f"Failed to add pair of arguments for {toggle_map}."
        ) from _type_err
    return parser_in


def add_toggle_argument_group(
    some_parser: Union[argparse.ArgumentParser, argparse._ArgumentGroup],
    flag_key: str,
) -> Union[argparse.ArgumentParser, argparse._ArgumentGroup]:
    """Add a pair of toggle-flags to the given parser."""
    if flag_key in FORMAT_TOGGLE_FLAGS_MAP:
        _toggle_map: ToggleFlagMap = FORMAT_TOGGLE_FLAGS_MAP[flag_key]
        some_parser = _add_toggle_argument_group(
            parser_in=some_parser,
            arg_key=flag_key,
            toggle_map=_toggle_map,
        )
    else:
        raise ValueError(f"Invalid flag ID: {flag_key}") from None
    return some_parser


def add_all_toggle_argument_groups(
    some_parser: Union[argparse.ArgumentParser, argparse._ArgumentGroup],
) -> Union[argparse.ArgumentParser, argparse._ArgumentGroup]:
    """Add a pair of toggle-flags to the given parser."""
    for _flag_key in FORMAT_TOGGLE_FLAGS_MAP:
        some_parser = add_toggle_argument_group(
            some_parser=some_parser,
            flag_key=_flag_key,
        )
    return some_parser


__all__ = [
    """StoreMutuallyExclusiveToggleAction""",
    """add_all_toggle_argument_groups""",
    """add_mutually_exclusive_flag_pair""",
    """add_toggle_argument_group""",
]
