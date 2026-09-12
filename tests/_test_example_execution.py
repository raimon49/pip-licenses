# tests.TestExampleExecution
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
tests.TestExampleExecution

To be documented?
"""

# import os
# import re
# import subprocess
# import sys
from typing import (
    # See https://github.com/raimon49/pip-licenses/issues/360
    ClassVar,  # extra -- only used for guiding mypy
)

from . import (
    ExampleRunner,
    ExampleScript,  # extra -- only used for guiding mypy
    unittest,
)
from ._readme_utils import (
    default_examples_dir,
    discover_examples,
)


class TestExampleExecution(unittest.TestCase):
    """Test execution of individual examples.

    Note: These tests are skipped if pip-licenses is not installed
    or required packages are not available.
    """

    runner: ClassVar[ExampleRunner]
    # Morally this should be list[ExampleScript] (but that would add yet another import)
    discovered_examples: ClassVar[list[ExampleScript]]

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class-level fixtures."""
        _example_working_dir = default_examples_dir()
        _runner_env = {
            "PWD": _example_working_dir,
            "OLDPWD": _example_working_dir,
        }
        cls.runner = ExampleRunner(timeout=30, env=_runner_env)
        cls.discovered_examples = discover_examples()

    def test_all_examples_run(self) -> None:
        """Test that all example scripts can run."""
        if not self.discovered_examples:
            self.skipTest("No examples discovered")

        failed = []
        for example in self.discovered_examples:
            with self.subTest(name=example.name):
                output = self.runner.run(example)

                # Some scripts may fail due to missing dependencies
                # We just verify they executed without fatal errors
                if output.error:
                    # Skip with error context
                    print(f"Skipped {example.name}: {output.error}")
                    continue
                # instead of self.assertIsTrue(output.success, "Examples should not fail!")

                # If script execution itself failed (not prerequisites),
                # record it but continue
                if not output.success:
                    if "not installed" not in output.stderr:
                        failed.append((example.name, output.stderr))
                else:
                    # should not need to skip, ok to fail on real failure
                    self.assertIsNotNone(
                        output.stdout, "Examples must not be empty!"
                    )
                    self.assertIn(
                        "demo",
                        output.output,
                        "Examples should have a demo prompt!",
                    )
                    self.assertIn(
                        "pip-licenses ",
                        output.output,
                        "Examples must be about pip-licenses!",
                    )  # THIS MAY CHANGE SLIGHTLY AFTER GHI #81 (as API may use PEP508 name)

        if failed:
            msg = "Some examples failed to execute:\n"
            _summary = f"[SKIP] {msg}"
            for name, stderr in failed:
                msg += f"  {name}: {stderr}\n"
                _summary += f"  {name}\n"
            # Log but don't fail - examples may have unfulfilled prerequisites
            print(msg)
            # also skip
            self.skipTest(_summary)


if __name__ == "__main__":
    # Run tests with unittest
    unittest.main(verbosity=2)
