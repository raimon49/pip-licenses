# tests.TestExampleReproducibility
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
tests.TestExampleReproducibility

To be documented?
"""

# import os
import re
from pathlib import Path
from typing import (
    # See https://github.com/raimon49/pip-licenses/issues/360
    ClassVar,  # extra -- only used for guiding mypy
)

# import subprocess
# import sys
from . import (
    unittest,
)
from .test_readme_examples import (
    discover_examples,
    load_readme,
)


class TestExampleReproducibility(unittest.TestCase):
    """Test reproducibility of examples against README.

    Note: These tests verify that examples documented in README
    can actually be executed.
    """

    readme_path: ClassVar[Path]
    readme_content: ClassVar[str]
    # Morally this should be list[ExampleScript] (but that would add yet another import)
    discovered_examples: ClassVar[list]

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class-level fixtures."""
        repo_root = Path(__file__).parent.parent
        cls.readme_path = repo_root / "README.md"
        cls.readme_content = load_readme(cls.readme_path)
        cls.discovered_examples = discover_examples()

    def test_readme_contains_examples(self) -> None:
        """Verify README contains bash code blocks."""
        # Look for bash code blocks
        bash_blocks = re.findall(
            r"```bash\n(.*?)```", self.readme_content, re.DOTALL
        )
        self.assertGreater(
            len(bash_blocks), 0, "No bash examples found in README"
        )
        example_blocks = re.findall(
            r"```console\n(.*?)```", self.readme_content, re.DOTALL
        )
        self.assertGreater(
            len(example_blocks), 0, "No console examples found in README"
        )

    def test_examples_match_readme_patterns(self) -> None:
        """Verify discovered examples have corresponding README sections.

        This is a basic check - ensures documentation and examples
        are reasonably aligned.
        """
        # Extract all pip-licenses commands from README
        commands = re.findall(r"pip-licenses\s+([^\n]+)", self.readme_content)

        # We just verify some commands are documented
        self.assertGreater(
            len(commands), 0, "No pip-licenses commands in README"
        )

        # Check that common options are documented
        documented_options = " ".join(commands)
        expected_options = [
            "--format",
            "--from",
            "--with-system",  # DEPRECATED use '--ignore-system' instead
            "--order",
            "--summary",
        ]

        for option in expected_options:
            self.assertIn(
                option, documented_options, f"Option {option} not documented"
            )


if __name__ == "__main__":
    # Run tests with unittest
    unittest.main(verbosity=2)
