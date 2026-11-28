# tests.test_cli_module
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


"""Test harness for CLI modules.

This module tests the internal cli components and their helpers.

1. Test format flag nomenclature
2. Test CLI migration helpers
3. Test RegexFlags helpers
4. Test Configuration prototype.

"""

from . import unittest
from ._test_cli_config import (
    ConfigurationTests,  # noqa: F401 -- Import as part of test API
    SerializationHelpersTests,  # noqa: F401 -- Import as part of test API
    SetOfStrTests,  # noqa: F401 -- Import as part of test API
    SplitLegacyTokensTests,  # noqa: F401 -- Import as part of test API
)

# MARK: Test Classes
from ._test_cli_migration_helpers import (
    TestMigrateWithSystemHelper,  # noqa: F401 -- Import as part of test API
)
from ._test_example_regex_flags import RegexFlagsTests  # noqa: F401 -- Import as part of test API
from ._test_format_config import TestFormatConfig  # noqa: F401 -- Import as part of test API
from ._test_format_nomenclature import (
    FormatConfigTests,  # noqa: F401 -- Import as part of test API
    FormatNomenclatureTests,  # noqa: F401 -- Import as part of test API
    MutuallyExclusiveToggleTests,  # noqa: F401 -- Import as part of test API
)

if __name__ == "__main__":
    # Run tests with unittest
    unittest.main(verbosity=2)
