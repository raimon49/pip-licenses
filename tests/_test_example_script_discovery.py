# tests.TestExampleScriptDiscovery
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
tests.TestExampleScriptDiscovery

To be documented?
"""

# import os
import re  # noqa: F401 -- used by TestExampleScriptDiscovery.test_example_script_naming
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
from ._readme_utils import (
    discover_examples,
)


class TestExampleScriptDiscovery(unittest.TestCase):
    """Test discovery of example scripts."""

    examples_dir: ClassVar[Path]
    # Morally this should be list[ExampleScript] (but that would add yet another import)
    discovered_examples: ClassVar[list]

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class-level fixtures."""
        repo_root = Path(__file__).parent.parent
        cls.examples_dir = repo_root / "docs" / "examples"
        cls.discovered_examples = discover_examples(cls.examples_dir)

    def test_examples_directory_exists(self) -> None:
        """Verify examples directory exists."""
        self.assertTrue(
            self.examples_dir.exists(),
            f"Examples directory not found: {self.examples_dir}",
        )
        self.assertTrue(
            self.examples_dir.is_dir(), f"Not a directory: {self.examples_dir}"
        )

    def test_discover_examples(self) -> None:
        """Verify examples are discovered."""
        self.assertGreater(
            len(self.discovered_examples), 0, "No examples discovered"
        )

        # Check that at least some expected scripts are found
        names = {ex.name for ex in self.discovered_examples}
        self.assertIn(
            "01-basic-usage.sh", names, "Basic usage example not found"
        )
        self.assertNotIn(
            "common.sh", names, "common.sh should not be in discovered scripts"
        )

    def test_examples_sorted(self) -> None:
        """Verify examples are sorted by number."""
        numbers = [ex.number for ex in self.discovered_examples]
        self.assertEqual(
            numbers, sorted(numbers), "Examples not sorted by number"
        )

    def test_example_script_naming(self) -> None:
        """Verify all examples follow naming convention."""
        for ex in self.discovered_examples:
            # Should match NN-descriptive-name.sh
            self.assertRegex(
                ex.name,
                r"^\d{2}-[a-z0-9-]+\.sh$",
                f"Script name doesn't follow convention: {ex.name}",
            )


if __name__ == "__main__":
    # Run tests with unittest
    unittest.main(verbosity=2)
