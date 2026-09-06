# tests.TestValidationIntegration
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
tests.TestValidationIntegration

To be documented?
"""

# import os
# import re
# import subprocess
# import sys
from pathlib import Path

from . import (
    ExampleOutput,
    ExampleScript,
    OutputValidator,
    unittest,
)
from .test_readme_examples import (
    load_readme,
)


class TestValidationIntegration(unittest.TestCase):
    """Integration tests for validation framework."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.validator = OutputValidator()
        self.pinnedName = "Django"
        self.pinnedVersion = "6.0.6"
        self.PinnedExpectedLicense = "BSD-3-Clause"

    def test_validator_success_validation(self) -> None:
        """Test success validation logic."""
        # Create a successful output
        script = ExampleScript.from_path(Path("./01-basic-usage.sh"))
        output = ExampleOutput(
            script=script,
            exit_code=0,
            stdout=f"Name    Version  License\n{self.pinnedName}  {self.pinnedVersion}    {self.PinnedExpectedLicense}",
            stderr="",
        )

        success, msg = self.validator.validate_success(output)
        self.assertTrue(success, f"Validation failed: {msg}")

    def test_validator_failure_detection(self) -> None:
        """Test failure detection."""
        script = ExampleScript.from_path(Path("./01-basic-usage.sh"))
        output = ExampleOutput(
            script=script,
            exit_code=1,
            stdout="",
            stderr="Error: pip-licenses not found",
        )

        success, msg = self.validator.validate_success(output)
        self.assertFalse(success, "Should detect failure")
        self.assertIn(
            "Non-zero exit code", msg, f"Expected exit code in message: {msg}"
        )

    def test_validator_readme_check(self) -> None:
        """Test README validation."""
        readme_content = load_readme()
        script = ExampleScript.from_path(Path("./01-basic-usage.sh"))
        output = ExampleOutput(
            script=script,
            exit_code=0,
            stdout=f"Name    Version  License\n{self.pinnedName}  {self.pinnedVersion}    {self.PinnedExpectedLicense}",
            stderr="",
        )

        success, msg = self.validator.validate_in_readme(
            output, readme_content
        )
        self.assertTrue(success, f"README validation failed: {msg}")


if __name__ == "__main__":
    # Run tests with unittest
    unittest.main(verbosity=2)
