# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et
"""
pip-licenses.cli._argparse_bridge

MIT-0 License OR MIT License

Rationale: if the license is bigger than the actual code, then MIT-0 is
sufficient, and compatible to just the MIT-0, so we'll be explicit here.

---

MIT No Attribution (MIT-0 License)

Copyright (c) 2026 Mr. Walls

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import argparse

from ._flags import (
    FORMAT_TOGGLE_FLAGS_MAP,
    ToggleFlagMap,
)


def _add_toggle_argument_group(
    parser_in: argparse.ArgumentParser,
    arg_key: str,
    toggle_map: ToggleFlagMap,
) -> argparse.ArgumentParser:
    """Not part of the public API."""
    some_toggle_group = parser_in.add_mutually_exclusive_group()
    some_toggle_group.add_argument(
        toggle_map["enable"],
        action="store_true",
        dest=toggle_map["config_dest"],
        default=toggle_map["initial"],
        help=f"output with package {arg_key}",
    )
    some_toggle_group.add_argument(
        toggle_map["disable"],
        action="store_false",
        dest=toggle_map["config_dest"],
        default=toggle_map["initial"],
        help=f"omit package {arg_key}",
    )
    return parser_in


def add_toggle_argument_group(
    some_parser: argparse.ArgumentParser,
    flag_key: str,
) -> argparse.ArgumentParser:
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
    some_parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Add a pair of toggle-flags to the given parser."""
    for _flag_key in FORMAT_TOGGLE_FLAGS_MAP:
        some_parser = add_toggle_argument_group(
            some_parser=some_parser,
            flag_key=_flag_key,
        )
    return some_parser


__all__ = [
    """add_all_toggle_argument_groups""",
    """add_toggle_argument_group""",
    """argparse""",  # the module
]
