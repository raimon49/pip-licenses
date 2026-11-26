# tests._test_example_regex_flags
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


"""
tests._test_example_regex_flags

Test internal helper class.
"""

import re

from piplicenses.cli._regex_flag import (
    _RESERVED_INVALID_PATTERN,
    RegexFlags,
    _is_pattern,
)

from . import unittest


class ExampleRegexFlags(RegexFlags):
    ZERO = 0, re.compile("zero")
    ALPHA = 1, re.compile("alpha")
    DIGIT = 2, re.compile("digit")
    BOTH = (
        3,
        RegexFlags._any_regex_helper(
            re.compile("alpha"),
            re.compile("digit"),
        ),
    )


class RegexFlagsTests(unittest.TestCase):
    def test_member_stores_its_pattern(self) -> None:
        self.assertEqual(ExampleRegexFlags.ALPHA.pattern.pattern, "alpha")

    def test_regex_for_single_member(self) -> None:
        regex = ExampleRegexFlags.ALPHA.regex

        self.assertEqual(regex.pattern, "(?:alpha)")
        self.assertTrue(regex.fullmatch("alpha"))

    def test_regex_for_combined_members(self) -> None:
        regex = (ExampleRegexFlags.ALPHA | ExampleRegexFlags.DIGIT).regex

        self.assertEqual(regex.pattern, "(?:alpha)|(?:digit)")
        self.assertTrue(regex.fullmatch("alpha"))
        self.assertTrue(regex.fullmatch("digit"))
        self.assertIsNone(regex.fullmatch("other"))

    def test_zero_value_uses_reserved_invalid_pattern(self) -> None:
        self.assertIs(ExampleRegexFlags.ZERO.regex, _RESERVED_INVALID_PATTERN)
        self.assertEqual(ExampleRegexFlags.ZERO.regex.pattern, "(?!)")

    def test_format_uses_regex_pattern(self) -> None:
        self.assertEqual(
            format(ExampleRegexFlags.ALPHA, ">12"), "   (?:alpha)"
        )
        self.assertEqual(format(ExampleRegexFlags.ZERO), "(?!)")

    def test_str_returns_pattern_or_empty_string_for_zero(self) -> None:
        self.assertEqual(str(ExampleRegexFlags.ALPHA), "(?:alpha)")
        self.assertEqual(str(ExampleRegexFlags.ZERO), "")

    def test_repr_includes_member_name_and_pattern(self) -> None:
        self.assertEqual(
            repr(ExampleRegexFlags.ALPHA),
            "<piplicenses.RegexFlags.ALPHA object; regex=(?:alpha)>",
        )

    def test_repr_for_zero_omits_pattern(self) -> None:
        self.assertEqual(
            repr(ExampleRegexFlags.ZERO),
            "<piplicenses.RegexFlags.ZERO object>",
        )

    def test_new_rejects_non_pattern_member_value(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "pattern must be an instance of type re.Pattern",
        ):

            class InvalidRegexFlags(RegexFlags):
                INVALID = 1, "not a compiled pattern"  # type: ignore[assignment]

    def test_is_pattern_checks_for_compiled_pattern(self) -> None:
        self.assertTrue(_is_pattern(re.compile("alpha")))
        self.assertFalse(_is_pattern("alpha"))

    def test_helper_without_patterns_returns_reserved_pattern(self) -> None:
        self.assertIs(
            RegexFlags._any_regex_helper(),
            _RESERVED_INVALID_PATTERN,
        )

    def test_helper_combines_patterns_with_matching_flags(self) -> None:
        regex = RegexFlags._any_regex_helper(
            re.compile("alpha", re.IGNORECASE),
            re.compile("digit", re.IGNORECASE),
        )

        self.assertEqual(regex.pattern, "(?:alpha)|(?:digit)")
        self.assertEqual(regex.flags, re.compile("", re.IGNORECASE).flags)

    def test_helper_rejects_non_pattern(self) -> None:
        with self.assertRaisesRegex(
            TypeError, "All patterns must be instances"
        ):
            RegexFlags._any_regex_helper(re.compile("alpha"), "not a pattern")  # type: ignore[arg-type]

    def test_helper_rejects_patterns_with_different_flags(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "all patterns must use the same regex flags",
        ):
            RegexFlags._any_regex_helper(
                re.compile("alpha"),
                re.compile("digit", re.IGNORECASE),
            )


if __name__ == "__main__":
    unittest.main()
