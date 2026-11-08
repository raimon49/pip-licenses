# tests._readme_utils
#
# MIT License
#
# Copyright (c) 2026 Mr. Walls
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
#


"""Test utilities for README.md documentation example testing."""

import os
import re

# from dataclasses import dataclass
from pathlib import Path
from sys import stderr
from typing import Optional

from ._examples import (
    ExampleScript,
)

# MARK: Discovery Functions


def default_examples_dir() -> Path:
    """Convenience function to simplify finding the dir ../../docs/examples/"""
    _repo_root = Path(__file__).parent.parent
    _examples_dir = _repo_root / "docs" / "examples"

    if not _examples_dir.exists():
        msg = f"Examples directory not found: {_examples_dir}"
        raise FileNotFoundError(msg) from None

    return _examples_dir


def discover_examples(
    examples_dir: Optional[Path] = None,
) -> list[ExampleScript]:
    """Discover all example scripts in docs/examples/.

    Args:
        examples_dir: Override default examples directory

    Returns:
        Sorted list of ExampleScript instances

    Raises:
        FileNotFoundError: If examples directory doesn't exist
    """
    if examples_dir is None:
        examples_dir = default_examples_dir()
    # re-check to avoid TOCTOU race
    if not examples_dir.exists():
        msg = f"Examples directory not found: {examples_dir}"
        raise FileNotFoundError(msg) from None

    # see [https://regex101.com/r/Ea5FgZ/1](https://regex101.com/?regex=%5E%28%3F%3Cdirname%3E%28%3F%3CdirNum%3E%5B0-9%5D%2B%29%28%3F%3A%5Bx0-9%5D%29%3F%28%3F%3Cprefix%3E%5C-%5B%5E%5C%2F%5D*%29%29%28%3F%3A%5C%2F%29%28%3F%3Cfilename%3E%28%3F%3CfileNum%3E%28%3FP%3DdirNum%29%28%3F%3A%5B0-9%5D%3F%29%29%28%3F%3A%28%3FP%3Dprefix%29%28%3F%3CbaseName%3E%5B%5E%5C%2F%5D*%29%5C.sh%29%29%24&testString=00-demo%2F00-example-demo.sh%0A01-basic%2F01-basic-usage.sh%0A02-usage%2F02-usage-venv.sh%0A10-option-order%2F10-option-order-licenese.sh%0A10-option-order%2F11-option-order-name.sh%0A13-junk%2Fnot-a-13-match.sh%0A13-junk%2Fjunk-also-not-a-match.sh%0A13-junk%2F43-not-a-match.sh%0A20-format%2F20-format-markdown.sh%0A20-format%2F21-format-rst.sh%0A20-format%2F22-format-confluence.sh%0A20-format%2F23-format-html.sh%0A20-format%2F24-format-json.sh%0A20-format%2F25-format-json-licensefinder.sh%0A20-format%2F26-format-csv.sh%0A20-format%2F27-format-plain-vertical.sh&flags=gm&flavor=pcre2&delimiter=%2F)
    _PATTERN = r"""^(?P<dirname>(?P<dirNum>[0-9]+)(?:[x0-9])?(?P<prefix>\-[^\/]*))(?:\/)(?P<filename>(?P<fileNum>(?P=dirNum)(?:[0-9]?))(?:(?P=prefix)(?P<baseName>[^\/]*)\.sh))$"""
    # Python's `re` syntax uses (?P<name>...) for named groups and
    # (?P=name) for named backreferences.
    pattern = re.compile(
        _PATTERN,
        re.VERBOSE,
    )

    scripts: list[ExampleScript] = []

    # Use paths relative to examples_dir because the regex includes the
    # directory name, e.g. "01-basic/01-basic-usage.sh".
    for script_path in examples_dir.rglob("*.sh"):
        if not script_path.is_file():
            continue

        # mod_path = script_path.relative_to(os.getcwd()).as_posix()
        relative_path = script_path.relative_to(examples_dir).as_posix()

        if pattern.fullmatch(relative_path) is None:
            continue

        try:
            dot_path = Path(os.getcwd())
            full_script_path = (
                dot_path / script_path.relative_to(os.getcwd()).as_posix()
            )
            scripts.append(ExampleScript.from_path(full_script_path))
        except ValueError as e:
            print(f"Skipping {script_path}: {e}", file=stderr)

    return sorted(scripts)


def load_readme(readme_path: Optional[Path] = None) -> str:
    """Load README.md content.

    Args:
        readme_path: Override default README path

    Returns:
        Full README.md content

    Raises:
        FileNotFoundError: If README doesn't exist
    """
    if readme_path is None:
        repo_root = Path(__file__).parent.parent
        readme_path = repo_root / "README.md"

    if not readme_path.exists():
        msg = f"README not found: {readme_path}"
        raise FileNotFoundError(msg)

    with open(readme_path, encoding="utf-8") as f:
        return f.read()


__all__ = [
    """default_examples_dir""",
    """discover_examples""",
    """load_readme""",
]
