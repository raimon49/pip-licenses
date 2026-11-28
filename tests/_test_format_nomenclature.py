# tests._test_format_nomenclature
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
tests._test_format_nomenclature

Test internal nomenclature helper utils behavior.
"""

from piplicenses.cli import (  # noqa: I001 -- order matters
    _format_config,
    _format_nomenclature,
    _mutually_exclusive_toggle,
)

# These need to be placed AFTER users of _argparse_bridge to guide linters
# ... rather than as an absolute import anywhere.
from argparse import (
    ArgumentParser,
    Namespace,
)

from . import unittest

# and this must be AFTER importing unittest.
from unittest.mock import patch


class FormatNomenclatureTests(unittest.TestCase):
    def test_require_nonempty_string_rejects_non_string(self) -> None:
        with self.assertRaisesRegex(TypeError, "must be a string"):
            _format_nomenclature._require_nonempty_string(None, "hint")

    def test_require_nonempty_string_rejects_empty_string(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            _format_nomenclature._require_nonempty_string("", "hint")

    def test_require_nonempty_string_rejects_falsey_nonempty_subclass(
        self,
    ) -> None:
        class FalseyString(str):
            def __bool__(self) -> bool:
                return False

        with self.assertRaisesRegex(ValueError, "must not be false-y"):
            _format_nomenclature._require_nonempty_string(
                FalseyString("value"), "hint"
            )

    def test_require_nonempty_string_returns_valid_string(self) -> None:
        self.assertEqual(
            _format_nomenclature._require_nonempty_string("value", "hint"),
            "value",
        )

    def test_normalize_to_config_form(self) -> None:
        cases = [
            ("--With-License-Files--", "with_license_files"),
            ("  Mixed.Case  ", "mixed.case"),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(
                    _format_nomenclature._normalize_to_config_form(value),
                    expected,
                )

    def test_normalize_to_config_form_rejects_invalid_values(self) -> None:
        for value, exception in ((None, TypeError), ("", ValueError)):
            with self.subTest(value=value), self.assertRaises(exception):
                # test actual runtime type behavior (static types mean nothing here)
                _format_nomenclature._normalize_to_config_form(value)  # type: ignore[arg-type]

    def test_generate_all_config_forms(self) -> None:
        self.assertEqual(
            _format_nomenclature._generate_all_config_forms("My-Feature"),
            [
                "with_my_feature",
                "with_my_feature_files",
                "with_my_feature_paths",
            ],
        )

    def test_generate_only_config_form(self) -> None:
        self.assertEqual(
            _format_nomenclature._generate_only_config_form("My-Feature"),
            ["with_my_feature"],
        )

    def test_reduce_to_config_form_adds_prefix_when_missing(self) -> None:
        self.assertEqual(
            _format_nomenclature.reduce_to_config_form("license-files"),
            "with_license_files",
        )

    def test_reduce_to_config_form_canonicalizes_disable_prefix(self) -> None:
        self.assertEqual(
            _format_nomenclature.reduce_to_config_form("without-license"),
            "with_license",
        )

    def test_reduce_to_config_form_leaves_enable_prefix_canonical(
        self,
    ) -> None:
        self.assertEqual(
            _format_nomenclature.reduce_to_config_form("with-license"),
            "with_license",
        )

    def test_reduce_to_config_form_rejects_invalid_values(self) -> None:
        for value, exception in ((None, TypeError), ("", ValueError)):
            with self.subTest(value=value), self.assertRaises(exception):
                # test actual runtime type behavior (static types mean nothing here)
                _format_nomenclature.reduce_to_config_form(value)  # type: ignore[arg-type]

    def test_generate_config_mapping(self) -> None:
        self.assertEqual(
            _format_nomenclature.generate_config_mapping("My-Feature"),
            {
                "field": "with_my_feature",
                "files": "with_my_feature_files",
                "paths": "with_my_feature_paths",
            },
        )

    def test_generate_config_mapping_rejects_empty_hint(self) -> None:
        with self.assertRaises(ValueError):
            _format_nomenclature.generate_config_mapping("")

    def test_generate_expected_config_forms_with_and_without_overrides(
        self,
    ) -> None:
        self.assertEqual(
            _format_nomenclature._generate_expected_config_forms(
                "thing", True
            ),
            ["with_thing", "with_thing_files", "with_thing_paths"],
        )
        self.assertEqual(
            _format_nomenclature._generate_expected_config_forms(
                "thing", False
            ),
            ["with_thing"],
        )

    def test_generate_toggle_flag_forms(self) -> None:
        self.assertEqual(
            _format_nomenclature._generate_toggle_flag_forms("thing"),
            ["--with-thing", "--without-thing"],
        )

    def test_generate_all_flag_forms(self) -> None:
        self.assertEqual(
            _format_nomenclature._generate_all_flag_forms("thing"),
            [
                "--with-thing",
                "--without-thing",
                "--with-thing-files",
                "--without-thing-files",
                "--with-thing-paths",
                "--without-thing-paths",
            ],
        )

    def test_generate_flag_forms_reject_empty_hint(self) -> None:
        for func in (
            _format_nomenclature._generate_toggle_flag_forms,
            _format_nomenclature._generate_all_flag_forms,
        ):
            _fname: str = func.__name__
            with self.subTest(function=_fname), self.assertRaises(ValueError):
                func("")

    def test_generate_expected_flag_forms_with_and_without_overrides(
        self,
    ) -> None:
        self.assertEqual(
            _format_nomenclature._generate_expected_flag_forms("thing", True),
            _format_nomenclature._generate_all_flag_forms("thing"),
        )
        self.assertEqual(
            _format_nomenclature._generate_expected_flag_forms("thing", False),
            _format_nomenclature._generate_toggle_flag_forms("thing"),
        )


class FormatConfigTests(unittest.TestCase):
    def test_split_categories_into_list(self) -> None:
        self.assertEqual(
            _format_config._split_categories_into_list(
                _format_config.FileCategory.AUTHORS
                | _format_config.FileCategory.LEGACY
            ),
            [
                _format_config.FileCategory.AUTHORS,
                _format_config.FileCategory.LEGACY,
            ],
        )
        self.assertEqual(
            _format_config._split_categories_into_list(
                _format_config.FileCategory.METADATA
            ),
            [],
        )
        self.assertEqual(
            _format_config._split_categories_into_list(
                _format_config.FileCategory.ANY
            ),
            [
                _format_config.FileCategory.ATTRIBUTION,
                _format_config.FileCategory.AUTHORS,
                _format_config.FileCategory.LEGACY,
                _format_config.FileCategory.NOTICES,
                _format_config.FileCategory.OTHERS,
            ],
        )
        self.assertEqual(
            _format_config._split_categories_into_list(
                _format_config.FileCategory(0)
            ),
            [],
        )

    def test_category_enable_prefix_maps_supported_categories(self) -> None:
        cases = [
            (_format_config.FileCategory.ATTRIBUTION, "attribution"),
            (_format_config.FileCategory.AUTHORS, "authors"),
            (_format_config.FileCategory.LEGACY, "legacy"),
            (_format_config.FileCategory.LICENSES, "license"),
            (_format_config.FileCategory.NOTICES, "notice"),
            (_format_config.FileCategory.OTHERS, "other"),
        ]
        for category, expected in cases:
            with self.subTest(category=category):
                self.assertEqual(
                    _format_config._category_enable_prefix(category),
                    expected,
                )

    def test_category_enable_prefix_rejects_empty_and_composite(self) -> None:
        with self.assertRaises(TypeError):
            _format_config._category_enable_prefix(
                _format_config.FileCategory(0)
            )
        with self.assertRaises(ValueError):
            _format_config._category_enable_prefix(
                _format_config.FileCategory.AUTHORS
                | _format_config.FileCategory.LEGACY
            )

    def test_category_files_and_paths_prefixes(self) -> None:
        cases = [
            (_format_config.FileCategory.ATTRIBUTION, "attribution"),
            (_format_config.FileCategory.AUTHORS, "authors"),
            (_format_config.FileCategory.LEGACY, "legacy"),
            (_format_config.FileCategory.LICENSES, "license"),
            (_format_config.FileCategory.NOTICES, "notice"),
            (_format_config.FileCategory.OTHERS, "other"),
        ]
        for category, expected in cases:
            with self.subTest(category=category):
                self.assertEqual(
                    _format_config._category_files_prefix(category),
                    expected,
                )
                self.assertEqual(
                    _format_config._category_paths_prefix(category),
                    expected,
                )

    def test_category_files_prefix_rejects_invalid_categories(self) -> None:
        with self.assertRaises(ValueError):
            _format_config._category_files_prefix(
                _format_config.FileCategory(0)
            )
        with self.assertRaises(AttributeError):
            _format_config._category_files_prefix(
                _format_config.FileCategory.AUTHORS
                | _format_config.FileCategory.LEGACY
            )

    def test_effective_bool_tri_state_and_coercion(self) -> None:
        self.assertIsNone(
            _format_config._effective_bool(Namespace(), "missing")
        )
        self.assertTrue(
            _format_config._effective_bool(
                Namespace(value=None), "value", default=True
            )
        )
        self.assertFalse(
            _format_config._effective_bool(
                Namespace(value=None), "value", default=False
            )
        )
        self.assertIs(
            _format_config._effective_bool(Namespace(value=True), "value"),
            True,
        )
        self.assertIs(
            _format_config._effective_bool(Namespace(value=False), "value"),
            False,
        )
        self.assertTrue(
            _format_config._effective_bool(Namespace(value=1), "value")
        )
        self.assertFalse(
            _format_config._effective_bool(Namespace(value=0), "value")
        )

    def test_tri_state_and_global_state_helpers(self) -> None:
        args = Namespace(with_files=True, with_paths=False, custom=None)
        self.assertIsNone(_format_config._tri_state(args, "custom"))
        self.assertTrue(_format_config._global_files_state(args))
        self.assertFalse(_format_config._global_paths_state(args))

    def test_category_state_and_local_override_states(self) -> None:
        category = _format_config.FileCategory.LICENSES
        self.assertTrue(_format_config._category_state(Namespace(), category))
        self.assertFalse(
            _format_config._category_state(
                Namespace(with_license=False), category
            )
        )
        self.assertTrue(
            _format_config._category_files_state(
                Namespace(with_license_files=True), category
            )
        )
        self.assertFalse(
            _format_config._category_paths_state(
                Namespace(with_license_paths=False), category
            )
        )

    def test_summary_active(self) -> None:
        self.assertFalse(_format_config._summary_active(Namespace()))
        self.assertFalse(
            _format_config._summary_active(Namespace(summary=False))
        )
        self.assertTrue(
            _format_config._summary_active(Namespace(summary=True))
        )

    def test_apply_effective_bit_preserves_unspecified_values(self) -> None:
        self.assertEqual(
            _format_config._apply_effective_bit(
                current_files=True,
                current_paths=False,
                files_setting=None,
                paths_setting=None,
            ),
            (True, False),
        )

    def test_apply_effective_bit_applies_explicit_values(self) -> None:
        self.assertEqual(
            _format_config._apply_effective_bit(
                current_files=False,
                current_paths=False,
                files_setting=True,
                paths_setting=False,
            ),
            (True, False),
        )

    def test_apply_single_flag_covers_noop_enable_and_disable(self) -> None:
        none = _format_config.FileFormat.SHOW_NONE
        both = _format_config.FileFormat.SHOW_BOTH
        contents = _format_config.FileFormat.SHOW_CONTENTS
        paths = _format_config.FileFormat.SHOW_PATHS

        self.assertEqual(
            _format_config._apply_single_flag(
                both, value=None, show_files=True, show_paths=True
            ),
            both,
        )
        self.assertEqual(
            _format_config._apply_single_flag(
                none, value=True, show_files=True, show_paths=True
            ),
            both,
        )
        self.assertEqual(
            _format_config._apply_single_flag(
                none, value=True, show_files=True, show_paths=False
            ),
            contents,
        )
        self.assertEqual(
            _format_config._apply_single_flag(
                none, value=True, show_files=False, show_paths=True
            ),
            paths,
        )
        self.assertEqual(
            _format_config._apply_single_flag(
                both, value=False, show_files=True, show_paths=True
            ),
            none,
        )
        self.assertEqual(
            _format_config._apply_single_flag(
                both, value=False, show_files=True, show_paths=False
            ),
            paths,
        )
        self.assertEqual(
            _format_config._apply_single_flag(
                both, value=False, show_files=False, show_paths=True
            ),
            contents,
        )

    def test_resolve_category_output_bits_uses_category_and_overrides(
        self,
    ) -> None:
        category = _format_config.FileCategory.LICENSES
        self.assertEqual(
            _format_config._resolve_category_output_bits(
                Namespace(), category
            ),
            (True, True),
        )
        self.assertEqual(
            _format_config._resolve_category_output_bits(
                Namespace(with_license=False), category
            ),
            (False, False),
        )
        self.assertEqual(
            _format_config._resolve_category_output_bits(
                Namespace(
                    with_license=True,
                    with_license_files=False,
                    with_license_paths=True,
                ),
                category,
            ),
            (False, True),
        )
        self.assertEqual(
            _format_config._resolve_category_output_bits(
                Namespace(with_files=False, with_paths=True), category
            ),
            (False, True),
        )

    def test_resolve_file_format_and_formats(self) -> None:
        self.assertEqual(
            _format_config.resolve_file_format(
                Namespace(),
                category=_format_config.FileCategory.LICENSES,
            ),
            _format_config.FileFormat.SHOW_NONE,
        )
        result = _format_config.resolve_file_formats(Namespace())
        self.assertEqual(
            set(result),
            {
                _format_config.FileCategory.ATTRIBUTION,
                _format_config.FileCategory.AUTHORS,
                _format_config.FileCategory.LEGACY,
                _format_config.FileCategory.LICENSES,
                _format_config.FileCategory.NOTICES,
                _format_config.FileCategory.OTHERS,
            },
        )
        self.assertTrue(
            all(
                value == _format_config.FileFormat.SHOW_NONE
                for value in result.values()
            )
        )

    def test_validate_namespace_summary_short_circuits(self) -> None:
        parser = ArgumentParser()
        _format_config.validate_file_format_namespace(
            parser,
            Namespace(summary=True, with_files=True, with_license=False),
        )

    def test_validate_namespace_rejects_disabled_category_with_local_enable(
        self,
    ) -> None:
        parser = ArgumentParser()
        with self.assertRaises(SystemExit):
            _format_config.validate_file_format_namespace(
                parser,
                Namespace(
                    with_license=False,
                    with_license_files=True,
                ),
            )

    def test_validate_namespace_rejects_global_enable_with_no_active_category(
        self,
    ) -> None:
        parser = ArgumentParser()
        all_categories_disabled = dict.fromkeys(
            (
                _format_config.FileCategory.ATTRIBUTION,
                _format_config.FileCategory.AUTHORS,
                _format_config.FileCategory.LEGACY,
                _format_config.FileCategory.LICENSES,
                _format_config.FileCategory.NOTICES,
                _format_config.FileCategory.OTHERS,
            ),
            _format_config.FileFormat.SHOW_NONE,
        )
        with (
            patch.object(
                _format_config,
                "resolve_file_formats",
                return_value=all_categories_disabled,
            ),
            self.assertRaises(SystemExit),
        ):
            _format_config.validate_file_format_namespace(
                parser,
                Namespace(with_files=True),
            )

    def test_resolve_category_output_bits_for_non_license_categories(
        self,
    ) -> None:
        cases = [
            _format_config.FileCategory.ATTRIBUTION,
            _format_config.FileCategory.AUTHORS,
            _format_config.FileCategory.LEGACY,
            _format_config.FileCategory.NOTICES,
            _format_config.FileCategory.OTHERS,
        ]
        for category in cases:
            with self.subTest(category=category):
                self.assertEqual(
                    _format_config._resolve_category_output_bits(
                        Namespace(), category
                    ),
                    (False, False),
                )

    def test_resolve_category_format_rejects_unnamed_category(self) -> None:
        with self.assertRaisesRegex(ValueError, "Only named categories"):
            _format_config._resolve_category_format(
                Namespace(),
                category=_format_config.FileCategory(0),
            )


class MutuallyExclusiveToggleTests(unittest.TestCase):
    def test_argument_group_detection(self) -> None:
        parser = ArgumentParser()
        group = parser.add_argument_group("options")
        self.assertTrue(_mutually_exclusive_toggle._is_argument_group(group))
        self.assertFalse(_mutually_exclusive_toggle._is_argument_group(parser))

    def test_valid_argument_container_accepts_parser_and_group(self) -> None:
        parser = ArgumentParser()
        group = parser.add_argument_group("options")
        self.assertTrue(
            _mutually_exclusive_toggle._is_valid_argument_container(parser)
        )
        self.assertTrue(
            _mutually_exclusive_toggle._is_valid_argument_container(group)
        )

    def test_valid_argument_container_rejects_wrong_type(self) -> None:
        with self.assertRaisesRegex(TypeError, "parser is of the wrong type"):
            _mutually_exclusive_toggle._is_valid_argument_container(object())

    def test_add_mutually_exclusive_flag_pair_sets_defaults_and_values(
        self,
    ) -> None:
        parser = ArgumentParser()
        result = _mutually_exclusive_toggle.add_mutually_exclusive_flag_pair(
            parser,
            enable_flag="--with-feature",
            disable_flag="--without-feature",
            dest="feature",
            help_text="feature output",
            default=None,
        )
        self.assertIs(result, parser)

        self.assertIsNone(parser.parse_args([]).feature)
        self.assertTrue(parser.parse_args(["--with-feature"]).feature)
        self.assertFalse(parser.parse_args(["--without-feature"]).feature)

    def test_add_mutually_exclusive_flag_pair_rejects_both_flags(self) -> None:
        parser = ArgumentParser()
        _mutually_exclusive_toggle.add_mutually_exclusive_flag_pair(
            parser,
            enable_flag="--with-feature",
            disable_flag="--without-feature",
            dest="feature",
            help_text="feature output",
        )
        with self.assertRaises(SystemExit):
            parser.parse_args(["--with-feature", "--without-feature"])

    def test_add_mutually_exclusive_flag_pair_wraps_argument_type_error(
        self,
    ) -> None:
        class BrokenGroup:
            def add_argument(self, *args: object, **kwargs: object) -> None:
                raise TypeError("bad argument")

        class BrokenParser:
            def add_mutually_exclusive_group(self) -> BrokenGroup:
                return BrokenGroup()

        with self.assertRaisesRegex(ValueError, "Failed to add pair"):
            # test actual runtime error behavior (static types mean nothing here)
            _mutually_exclusive_toggle.add_mutually_exclusive_flag_pair(
                BrokenParser(),  # type: ignore[arg-type]
                enable_flag="--with-feature",
                disable_flag="--without-feature",
                dest="feature",
                help_text="feature output",
            )

    def test_store_action_updates_namespace_and_validates(self) -> None:
        parser = ArgumentParser()
        _mutually_exclusive_toggle.add_mutually_exclusive_flag_pair(
            parser,
            enable_flag="--with-feature",
            disable_flag="--without-feature",
            dest="feature",
            help_text="feature output",
        )

        with patch.object(
            _mutually_exclusive_toggle, "validate_file_format_namespace"
        ) as validate:
            self.assertTrue(parser.parse_args(["--with-feature"]).feature)
            validate.assert_called_once()

        with patch.object(
            _mutually_exclusive_toggle, "validate_file_format_namespace"
        ):
            self.assertFalse(parser.parse_args(["--without-feature"]).feature)

    def test_add_toggle_argument_group_rejects_unknown_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid flag ID"):
            _mutually_exclusive_toggle.add_toggle_argument_group(
                ArgumentParser(), "not-a-flag"
            )

    def test_add_toggle_argument_group_wraps_type_error(self) -> None:
        with (
            patch.object(
                _mutually_exclusive_toggle,
                "add_mutually_exclusive_flag_pair",
                side_effect=TypeError("bad parser"),
            ),
            self.assertRaisesRegex(ValueError, "Failed to add pair"),
        ):
            _mutually_exclusive_toggle._add_toggle_argument_group(
                ArgumentParser(),
                "feature",
                {
                    "enable": "--with-feature",
                    "disable": "--without-feature",
                    "initial": None,
                    "config_dest": "with_feature",
                },
            )

    def test_add_toggle_argument_group_and_all_groups(self) -> None:
        parser = ArgumentParser()
        self.assertIs(
            _mutually_exclusive_toggle.add_toggle_argument_group(
                parser,
                "licenses",
            ),
            parser,
        )
        all_parser = ArgumentParser()
        self.assertIs(
            _mutually_exclusive_toggle.add_all_toggle_argument_groups(
                all_parser,
            ),
            all_parser,
        )
        parsed = all_parser.parse_args([])
        self.assertTrue(hasattr(parsed, "with_licenses"))


# __all__ = [
#     """FormatConfigTests""",
#     """FormatNomenclatureTests""",
#     """MutuallyExclusiveToggleTests""",
# ]

if __name__ == "__main__":
    # Run tests with unittest
    unittest.main(verbosity=2)
