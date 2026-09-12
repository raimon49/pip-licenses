# tests.TestReadmeLoading
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
tests.TestReadmeLoading

To be documented?
"""

# import os
# import re
# import subprocess
# import sys
from pathlib import Path
from typing import (
    # See https://github.com/raimon49/pip-licenses/issues/360
    ClassVar,  # extra -- only used for guiding mypy
)

from . import (
    unittest,
)
from ._readme_utils import (
    load_readme,
)


class TestReadmeLoading(unittest.TestCase):
    """Test README loading and validation."""

    readme_path: ClassVar[Path]
    readme_content: ClassVar[str]

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class-level fixtures."""
        repo_root = Path(__file__).parent.parent
        # TODO: change to use os.path.join and separator etc.
        cls.readme_path = repo_root / "README.md"
        cls.readme_content = load_readme(cls.readme_path)

    def test_readme_exists(self) -> None:
        """Verify README.md exists."""
        self.assertTrue(
            self.readme_path.exists(), f"README not found: {self.readme_path}"
        )
        self.assertTrue(
            self.readme_path.is_file(), f"Not a file: {self.readme_path}"
        )

    def test_readme_content_loaded(self) -> None:
        """Verify README content is loaded."""
        self.assertGreater(len(self.readme_content), 0, "README is empty")
        self.assertIn(
            "pip-licenses",
            self.readme_content,
            "README doesn't mention pip-licenses",
        )
        self.assertTrue(
            "console" in self.readme_content
            or "pip-licenses" in self.readme_content,
            "README doesn't contain examples",
        )


if __name__ == "__main__":
    # Run tests with unittest
    unittest.main(verbosity=2)
