# tests.test_spdx_helpers
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


"""Test harness for v6 spdx matching edge-cases."""

from piplicenses._license_expressions import parse_spdx_expression
from piplicenses.core import case_and_type_insensitive_set_diff_helper

from . import unittest


class ParseSpdxExpressionTests(unittest.TestCase):
    def test_parse_spdx_expression(self) -> None:
        cases = [
            ("a OR b", ("a", "b")),
            ("a AND b", ("a", "b")),
            ("(a OR b) AND c", ("a", "b", "c")),
            ("a AND b OR c", ("a", "b", "c")),
            ("((a OR b) AND (c OR d))", ("a", "b", "c", "d")),
            ("MIT WITH Classpath-exception-2.0", ("MIT",)),
            (
                "LicenseRef-custom OR DocumentRef-doc:LicenseRef-other",
                ("LicenseRef-custom", "DocumentRef-doc:LicenseRef-other"),
            ),
            ("mit oR BSD-3-Clause", ("mit", "BSD-3-Clause")),
        ]
        for expression, expected in cases:
            with self.subTest(expression=expression):
                self.assertEqual(parse_spdx_expression(expression), expected)

    def test_parser_rejects_malformed_or_partial_input(self) -> None:
        expressions = [
            "a OR",
            "a OR b trailing text",
            "(a OR b",
            "a AND OR b",
            "a WITH",
            "(a OR b) WITH exception",
            "a OR b @ c",
            "",
        ]
        for expression in expressions:
            with self.subTest(expression=expression):
                self.assertIsNone(parse_spdx_expression(expression))

    def test_expression_allow_only_requires_each_license(self) -> None:
        cases = [
            ("a OR b", {"a", "b"}, set()),
            ("a OR b", {"a"}, {"b"}),
            ("a OR b OR c", {"a", "b"}, {"c"}),
            ("a AND b", {"a", "b"}, set()),
            ("a AND b", {"a"}, {"b"}),
            ("(a OR b) AND c", {"a", "b", "c"}, set()),
            ("(a OR b) AND c", {"a", "b"}, {"c"}),
            ("MIT WITH Classpath-exception-2.0", {"mit"}, set()),
        ]
        for expression, allowed, missing in cases:
            with self.subTest(expression=expression, allowed=allowed):
                expected = {"; ".join(sorted(missing))} if missing else set()
                self.assertEqual(
                    case_and_type_insensitive_set_diff_helper(
                        {expression}, allowed
                    ),
                    expected,
                )

    def test_legacy_value_uses_whole_string_exact_match(self) -> None:
        legacy = "License text OR something not SPDX"
        self.assertEqual(
            case_and_type_insensitive_set_diff_helper(
                {legacy}, {"License text"}
            ),
            {legacy},
        )
        self.assertEqual(
            case_and_type_insensitive_set_diff_helper(
                {legacy}, {legacy.lower()}
            ),
            set(),
        )

    def test_multiple_ordinary_values_keep_at_least_one_match_semantics(
        self,
    ) -> None:
        self.assertEqual(
            case_and_type_insensitive_set_diff_helper(
                {"MIT License", "BSD License"},
                {"mit license"},
            ),
            {"BSD License"},
        )

    def test_partial_matching_is_not_expression_expanded(self) -> None:
        from piplicenses.sorting import case_insensitive_partial_match_set_diff

        expression = "a OR b"
        self.assertEqual(
            case_insensitive_partial_match_set_diff({expression}, {"a"}),
            set(),
        )


if __name__ == "__main__":
    # Run tests with unittest
    unittest.main()
