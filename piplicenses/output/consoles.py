# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et

# pip-licenses.output.consoles
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
pip-licenses.output.consoles

Console focused output definitions live here.
To be documented?
"""

import sys
from collections.abc import (
    Callable,
)  # See https://github.com/raimon49/pip-licenses/issues/360

# from pip-licenses.io.open -> _real_io_open -> open (mockable)
from .. import open
from . import (
    __pkgname__,  # noqa: F401 -- Re-export as part of data API
    __version__,  # noqa: F401 -- Re-export as part of data API
)

open: Callable = open  # type: ignore[has-type]  # noqa: PLW0127  # allow monkey patching

# placeholder for importing colors


def output_colored(code: str, text: str, is_bold: bool = False) -> str:
    """
    Create function to output with color sequence
    """
    if is_bold:
        code = f"1;{code}"

    return f"\033[{code}m{text}\033[0m"


def save_if_needs(output_file: str, output_string: str) -> None:
    """
    Save to path given by args

    Raises:
        SystemExit: on underling filesystem failures (OSError).
    """
    if output_file is None:
        return

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output_string)
            if not output_string.endswith("\n"):
                # Always end output files with a new line
                f.write("\n")

        sys.stdout.write(f"created path: {output_file}\n")
        sys.exit(0)
    except OSError as _cause:
        raise SystemExit("check path: --output-file\n", 1) from _cause


__all__ = [
    """output_colored""",
    """save_if_needs""",
]
