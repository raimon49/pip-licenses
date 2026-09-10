# tests.TestDocumentationStatus
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
tests.TestDocumentationStatus

To be documented?
"""

# import os
# import re
# import subprocess
# import sys
from . import (
    unittest,
)
from ._readme_utils import (
    discover_examples,
)


class TestDocumentationStatus(unittest.TestCase):
    """Provide information about documentation test coverage."""

    def test_print_discovered_examples(self) -> None:
        """Print all discovered examples (for CI/CD reporting)."""
        discovered = discover_examples()

        print("\n" + "=" * 70)
        print("DISCOVERED DOCUMENTATION EXAMPLES")
        print("=" * 70)

        for ex in discovered:
            print(f"  {ex.number:2d}. {ex.name}")

        print(f"\nTotal: {len(discovered)} examples")
        print("=" * 70)

        self.assertGreater(len(discovered), 0, "No examples discovered")


if __name__ == "__main__":
    # Run tests with unittest
    unittest.main(verbosity=2)
