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

Trivial testing to ensure there are automated examples (at all).
"""

from . import (
    unittest,
)
from ._readme_utils import (
    discover_examples,
)


class TestDocumentationStatus(unittest.TestCase):
    """Provide information about documentation test coverage."""

    def test_print_discovered_examples(self) -> None:
        """Print all discovered examples (for CI/CD reporting).

        Acceptance criteria: pass if more than 7 found, fail otherwise.
        """
        discovered = discover_examples()
        _width_value: int = 70
        print("\n" + "=" * _width_value)
        print("DISCOVERED DOCUMENTATION EXAMPLES")
        print("=" * _width_value)

        for ex in discovered:
            print(f"  {ex.number:2d}. {ex.name}")

        print(f"\nTotal: {len(discovered)} examples")
        print("=" * _width_value)
        # pre-checks
        self.assertGreater(len(discovered), 0, "No examples discovered")
        self.assertGreater(len(discovered), 1, "Expected multiple examples")
        # Rationale: there are at-least 7 categories with 1 or more examples:
        self.assertGreater(len(discovered), 7, "Expected multiple examples")


if __name__ == "__main__":
    # Run tests with unittest
    unittest.main(verbosity=2)
