# tests.test_cli_migration_helpers
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


"""Test harness for v6 migration helpers edge-cases."""

import warnings

# import the test fixtures
from piplicenses.cli import (
    _migrate_no_license_path_helper,
    _migrate_no_version_helper,
    _migrate_with_system_helper,
    _migrate_without_license_paths_helper,
)

from . import unittest


class TestMigrateWithSystemHelper(unittest.TestCase):
    def test_missing_key_returns_false_without_warning(self) -> None:
        for func in (
            _migrate_with_system_helper,
            _migrate_no_version_helper,
            _migrate_no_license_path_helper,
        ):
            with self.subTest(function=func.__name__):
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    result = func({})

                self.assertIs(result, False)
                self.assertEqual(caught, [])

    def test_false_sys_help_value_returns_false_without_warning(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = _migrate_with_system_helper({"with-system": False})

        self.assertIs(result, False)
        self.assertEqual(caught, [])

    def test_false_no_version_value_returns_false_without_warning(
        self,
    ) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = _migrate_no_version_helper({"no-version": False})

        self.assertIs(result, False)
        self.assertEqual(caught, [])

    def test_false_no_license_path_value_returns_false_without_warning(
        self,
    ) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = _migrate_no_license_path_helper(
                {"no-license-path": False}
            )

        self.assertIs(result, False)
        self.assertEqual(caught, [])

    def test_false_without_license_path_value_returns_true_without_warning(
        self,
    ) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = _migrate_without_license_paths_helper(
                {"without-license-paths": False}
            )

        self.assertIs(result, True)
        self.assertEqual(caught, [])

    def test_true_value_returns_true_and_warns(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = _migrate_with_system_helper({"with-system": True})

        self.assertIs(result, True)
        self.assertEqual(len(caught), 1)
        self.assertIs(caught[0].category, UserWarning)
        self.assertIn("use include-system instead", str(caught[0].message))
        self.assertIn("issues/349", str(caught[0].message))

    def test_true_value_no_version_returns_true_and_warns(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = _migrate_no_version_helper({"no-version": True})

        self.assertIs(result, True)
        self.assertEqual(len(caught), 1)
        self.assertIs(caught[0].category, UserWarning)
        self.assertIn("use without-version instead", str(caught[0].message))
        self.assertIn("issues/349", str(caught[0].message))

    def test_true_value_no_license_returns_true_and_warns(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = _migrate_no_license_path_helper({"no-license-path": True})

        self.assertIs(result, True)
        self.assertEqual(len(caught), 1)
        self.assertIs(caught[0].category, UserWarning)
        self.assertIn(
            "use with-license-paths=false instead", str(caught[0].message)
        )
        self.assertIn("issues/349", str(caught[0].message))

    def test_true_value_without_license_returns_false_and_warns(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = _migrate_without_license_paths_helper(
                {"without-license-paths": True}
            )

        self.assertIs(result, False)
        self.assertEqual(len(caught), 1)
        self.assertIs(caught[0].category, UserWarning)
        self.assertIn(
            "use with-license-paths=false instead", str(caught[0].message)
        )
        self.assertIn("issues/349", str(caught[0].message))

    def test_truthy_non_bool_value_is_returned_without_warning(self) -> None:
        # The function warns only when the value is exactly True.
        value = 1
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = _migrate_with_system_helper({"with-system": value})

        self.assertIs(result, value)
        self.assertEqual(caught, [])


if __name__ == "__main__":
    # Run tests with unittest
    unittest.main()
