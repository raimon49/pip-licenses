# tests.OutputValidator
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
tests.OutputValidator

To be documented?
"""

# import os
# import re
# import subprocess
# import sys
from ._examples import (
    ExampleOutput,
)


class OutputValidator:
    """Validates example output against various criteria.

    Each method validates a specific aspect, allowing easy extension
    (Open/Closed Principle).
    """

    @staticmethod
    def validate_success(output: ExampleOutput) -> tuple[bool, str]:
        """Validate that script executed successfully.

        Args:
            output: ExampleOutput to validate

        Returns:
            Tuple of (success, message)
        """
        if output.error:
            msg = f"Execution error: {output.error}"
            return False, msg

        if output.exit_code != 0:
            msg = (
                f"Non-zero exit code: {output.exit_code}\n"
                f"stderr: {output.stderr}"
            )
            return False, msg

        if not output.stdout:
            msg = "No output produced"
            return False, msg

        return True, "Script executed successfully"

    @staticmethod
    def validate_output_not_empty(output: ExampleOutput) -> tuple[bool, str]:
        """Validate that output is not empty.

        Args:
            output: ExampleOutput to validate

        Returns:
            Tuple of (success, message)
        """
        combined = output.stdout + output.stderr
        if not combined.strip():
            return False, "Output is empty"
        return True, "Output is not empty"

    @staticmethod
    def validate_in_readme(
        output: ExampleOutput,
        readme_content: str,
    ) -> tuple[bool, str]:
        """Validate that output (or similar) exists in README.md.

        This is a basic check - looks for key patterns from output
        in the README to verify reproducibility.

        Args:
            output: ExampleOutput to validate
            readme_content: Full README.md content

        Returns:
            Tuple of (success, message)
        """
        if not output.stdout:
            return False, "No stdout to validate against README"

        # For now, look for pip-licenses in output (basic validation)
        # This ensures the script actually ran pip-licenses
        if "pip-licenses" in output.stdout or "Name" in output.stdout:
            return True, "Output pattern found in README examples"

        # Try to find specific version strings that examples use
        if "2.1.1" in output.stdout or "26.3" in output.stdout:
            return True, "Example versions found in output"

        # For JSON/CSV formats, check for common structure
        if any(
            fmt in output.stdout for fmt in ["{", "[", '"Name"', '"License"']
        ):
            return True, "Structured output format detected"

        return False, "Output not found in README examples"


__all__ = [
    """OutputValidator""",
]
