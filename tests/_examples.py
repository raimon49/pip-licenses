# tests._examples
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


"""
tests._examples

To be documented?
"""

import re
import subprocess

# import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# import env hardening helpers for ExampleRunner
from ._example_env import (
    examples_env,
    sanitized_environment,
)

# MARK: Data Classes


@dataclass
class ExampleScript:
    """Represents a single example script.

    Attributes:
        path: Full path to the script
        name: Script filename (e.g., '01-basic-usage.sh')
        number: Numeric prefix (e.g., 1 from '01-basic-usage.sh')
    """

    path: Path
    name: str
    number: int

    @classmethod
    def from_path(cls, script_path: Path) -> "ExampleScript":
        """Create ExampleScript from file path.

        Args:
            script_path: Path to the script file

        Returns:
            ExampleScript instance

        Raises:
            ValueError: If script name doesn't match expected pattern
        """
        name = None  # was script_path.name
        # Extract numeric prefix from name like '01-basic-usage.sh'
        # see https://regex101.com/r/U4SbUa/2
        _PATTERN = r"""^(?P<fullexamplesdir>(?P<repopath>(?:\/)(?:(?:[-\w]+[^\/\b\W]*)(?:\/))*)?(?P<examplesdir>(?:docs)(?:\/)(?:examples)(?:\/)))?(?P<dirname>(?P<dirNum>[0-9]+)(?:[x0-9])?(?P<prefix>\-[^\/]*))(?:\/)(?P<filename>(?P<fileNum>(?P=dirNum)(?:[0-9]?))(?:(?P=prefix)(?P<baseName>[^\/]*)\.sh))$"""
        # Python's `re` syntax uses (?P<name>...) for named groups and
        # (?P=name) for named back-references.
        pattern = re.compile(
            _PATTERN,
            re.UNICODE | re.MULTILINE | re.VERBOSE,
        )
        _match_path = re.search(pattern, str(script_path.as_posix()))
        if _match_path:
            _groups = _match_path.groupdict()
            if "filename" in _groups:
                name = _groups["filename"]
        if not name:
            msg = f"Script path doesn't match expected pattern: {script_path.as_posix()}"
            raise ValueError(msg)
        match = re.match(r"(\d+)-", name)
        if not match:
            msg = f"Script name doesn't match expected pattern: {script_path.name}"
            raise ValueError(msg)

        number = int(match.group(1))
        return cls(path=script_path, name=name, number=number)

    def _sort_key(self) -> tuple[int, str]:
        return self.number, self.name

    def __lt__(self, other: "ExampleScript") -> bool:
        """Allow sorting by numeric prefix."""
        if not isinstance(other, ExampleScript):
            return NotImplemented
        return self._sort_key() < other._sort_key()

    def __le__(self, other: "ExampleScript") -> bool:
        if not isinstance(other, ExampleScript):
            return NotImplemented
        return self._sort_key() <= other._sort_key()

    def __gt__(self, other: "ExampleScript") -> bool:
        if not isinstance(other, ExampleScript):
            return NotImplemented
        return self._sort_key() > other._sort_key()

    def __ge__(self, other: "ExampleScript") -> bool:
        if not isinstance(other, ExampleScript):
            return NotImplemented
        return self._sort_key() >= other._sort_key()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExampleScript):
            return False  # never equal
        return self._sort_key() == other._sort_key()

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, ExampleScript):
            return True  # always unequal
        return self._sort_key() != other._sort_key()

    def __hash__(self) -> int:
        return hash(self._sort_key())


@dataclass
class ExampleOutput:
    """Result of executing an example script.

    Attributes:
        script: The ExampleScript that was executed
        exit_code: Script exit code (0 = success)
        stdout: Standard output from script
        stderr: Standard error from script
        error: Exception if execution failed
    """

    script: ExampleScript
    exit_code: int
    stdout: str
    stderr: str
    error: Optional[Exception] = None

    @property
    def success(self) -> bool:
        """Check if execution succeeded."""
        return self.exit_code == 0 and self.error is None

    @property
    def output(self) -> str:
        """Get combined stdout and stderr."""
        return self.stdout + self.stderr


# MARK: ExampleRunner


class ExampleRunner:
    """Executes example scripts and captures output.

    This abstraction allows different execution strategies without
    affecting test code (Open/Closed Principle).
    """

    def __init__(self, timeout: int = 30, env: Optional[dict] = None) -> None:
        """Initialize runner.

        Args:
            timeout: Maximum seconds to wait for script execution
            env: Environment variables for subprocess (uses current env if None)
        """
        self.timeout = timeout
        self.env = sanitized_environment(extra=env) if env else examples_env()

    def run(self, script: ExampleScript) -> ExampleOutput:
        """Execute an example script.

        Args:
            script: ExampleScript to execute

        Returns:
            ExampleOutput with results
        """
        _args = [
            "bash",
            "-c",
            f"source {script.path!s}",
        ]
        try:
            result = subprocess.run(
                _args,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=self.env,
                check=False,
            )

            return ExampleOutput(
                script=script,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except subprocess.TimeoutExpired as e:
            return ExampleOutput(
                script=script,
                exit_code=-1,
                stdout="",
                stderr=f"Timeout after {self.timeout}s",
                error=e,
            )
        except Exception as e:  # noqa: BLE001 -- intentional to limit exception blast radius
            return ExampleOutput(
                script=script,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                error=e,
            )


__all__ = [
    """ExampleOutput""",
    """ExampleRunner""",
    """ExampleScript""",
]
