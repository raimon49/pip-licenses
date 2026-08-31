#!/usr/bin/env python
# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et

# pip-licenses.__main__
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
piplicenses.__main__

The main entry-point to pip-licenses.

Usage to be documented. See the README.md for now.

"""

from typing import (
    Any,  # See https://github.com/raimon49/pip-licenses/issues/360
)

from . import (
    __pkgname__,
    __summary__,
    __version__,
)
from .cli import (
    Configuration,
    argparse,  # just need argparse.Namespace
    create_parser,
    sys,  # just need sys.stderr
)
from .output import (
    create_output_string,
    create_warn_string,
    save_if_needs,
)

# placeholder for other main entry point stuff E.g.,
# __module__ = "pip-licenses"

# --- normalize overrides into dict ---


def add_overrides(
    input_dict: dict[str, Any],
    obj: Any,  # noqa: ANN401 -- Dynamically typed at runtime
) -> dict[str, Any]:
    """Normalize overrides into dict.

    BETA: SUBJECT TO SUDDEN CHANGE. Utility to help override configurations
    when invoking `main`.

    TBD: This could allow use-cases like wrapping and extending pip-licenses.
    Still unclear if this is actually useful yet.
    See [GHI 81](https://github.com/raimon49/pip-licenses/issues/81).

    Arguments:
     - input_dict: dict -- Optional input dictionary to override
                           (e.g., from previous calls).
     - obj -- The overrides, can be a namespace.

    Returns:
        dict: a dictionary of the overrides.
    """
    _override_dict: dict[str, Any] = input_dict or {}
    if obj is None:
        return _override_dict
    if isinstance(obj, dict):
        _override_dict.update(obj)
    elif isinstance(obj, argparse.Namespace):
        _override_dict.update(vars(obj))
    else:
        # object with attributes
        _override_dict.update(vars(obj))
    return _override_dict


def main(*args: Any, **kwargs: Any) -> int:
    """The main function of `pip-licenses`.

    Typically just invoked with no arguments. Documentation for release WIP;

    Experimentally,
    this `main` now allows extracting inputs from *args / **kwargs too;
    See [GHI 81](https://github.com/raimon49/pip-licenses/issues/81).

    Supported call styles:
      * `main()`                           -> CLI argv (default; stable)
      * `main(argv=[...])`                 -> CLI argv override (split command-line arguments)
      * `main(flags=[...])`                -> extra argv tokens (dashed falgs)
      * `main(overrides={...})`            -> merge overrides (over CLI/flags)
      * `main(**values)`                   -> treated as overrides too (configuration dict-like)
    Also supports (mix & match):
      * main(["--from", "meta", ...])      -> argv passed positionally

    However, this implementation (v6.0.0a0-v6.0.0b8) was/is still a mess.
    """
    argv = kwargs.pop("argv", None)
    flags = kwargs.pop("flags", None)
    overrides = kwargs.pop("overrides", None)

    # If first positional arg looks like argv list/tuple of strings, accept it.
    if args:
        # simplest/most predictable: only allow a single positional argv-like argument
        if (
            argv is None
            and len(args) == 1
            and isinstance(args[0], (list, tuple))
        ):
            argv = list(args[0])
        else:
            raise TypeError(
                "main(*args, **kwargs) only supports: "
                "main(), main(argv=[...]), main(flags=[...]), main(overrides=...), "
                "or main([...]) as a single positional argv argument."
            ) from None

    if argv is None:
        argv = sys.argv[1:]  # mimic pre-v6.0 behavior

    if flags:
        argv = list(argv) + list(flags)
    parser = create_parser()
    cli_args = parser.parse_args(args=argv)

    # BETA: handle v6.0+ overrides
    overrides_parsed_as_dict: dict[str, Any] = {}
    if overrides:
        overrides_parsed_as_dict = add_overrides(
            overrides_parsed_as_dict, overrides
        )
    # any remaining kwargs are also treated as overrides
    overrides_parsed_as_dict.update(kwargs)

    # TODO: validate overrides

    # merge (CLI first, then overrides win)
    merged = dict(vars(cli_args))
    merged.update(overrides_parsed_as_dict)

    # TODO: re-validate merged
    _config: Configuration = Configuration(**merged)

    exit_code: int = 0
    try:
        output_string = create_output_string(_config)

        output_file = _config.output_file
        save_if_needs(output_file, output_string)

        # prior to v6.0.0b7 this exception was an actual sys.exit(int) call,
        # but as part of GHI-316 all sys.exit(int) calls were refactored
        # to raise SystemExit exceptions that can be caught and handled
        # eventually
    except SystemExit as _abort:
        exit_code = _abort.code if isinstance(_abort.code, int) else 1
        raise SystemExit(exit_code) from _abort  # mimic pre-v6.0 behavior

    print(output_string)
    # TODO: use warnings
    # TODO: define exit_code value(s?) for warnings (2 is arbitrary)
    warn_string = create_warn_string(_config)
    if warn_string:
        print(warn_string, file=sys.stderr)
        return 0 if "6.0." in __version__ else 2
    return 0


__all__ = [
    #    """__doc__""",
    #    """__file__""",
    #    """__loader__""",
    #    """__name__""",
    #    """__package__""",
    #    """__path__""",
    """__pkgname__""",
    #    """__spec__""",
    """__summary__""",
    """__version__""",
    """main""",
]


if __name__ == "__main__":  # pragma: no cover
    main()
