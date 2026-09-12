# tests.test_readme_examples
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


"""Test harness for README.md documentation examples.

This module tests the reproducibility and correctness of all examples
in docs/examples/ by:

1. Discovering all example scripts
2. Executing each one with proper environment setup
3. Capturing output
4. Verifying output exists in README.md (basic validation)
5. Reporting results

"""

from . import unittest

# MARK: Test Classes
from ._test_documentation_status import (
    TestDocumentationStatus,  # noqa: F401 -- Import as part of test API
)
from ._test_example_execution import (
    TestExampleExecution,  # noqa: F401 -- Import as part of test API
)
from ._test_example_reproducibility import (
    TestExampleReproducibility,  # noqa: F401 -- Import as part of test API
)
from ._test_example_script_discovery import (
    TestExampleScriptDiscovery,  # noqa: F401 -- Import as part of test API
)
from ._test_readme_loading import (
    TestReadmeLoading,  # noqa: F401 -- Import as part of test API
)
from ._test_validation_integration import (
    TestValidationIntegration,  # noqa: F401 -- Import as part of test API
)

if __name__ == "__main__":
    # Run tests with unittest
    unittest.main(verbosity=2)
