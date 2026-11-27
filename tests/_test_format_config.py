# tests._test_format_config
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


"""Unit tests for file-format configuration and precedence rules."""

import sys

# These need to be placed AFTER _argparse_bridge to guide linters
# ... rather than as an absolute import anywhere.
from argparse import (
    ArgumentParser,
    Namespace,
)

# and this must be AFTER importing unittest.
from unittest.mock import Mock

from piplicenses.cli import _format_config

from . import (
    argparse,  # noqa: F401 -- used by next import group
    unittest,
)

CATEGORIES = (
    _format_config.FileCategory.ATTRIBUTION,
    _format_config.FileCategory.AUTHORS,
    _format_config.FileCategory.LEGACY,
    _format_config.FileCategory.LICENSES,
    _format_config.FileCategory.NOTICES,
    _format_config.FileCategory.OTHERS,
)


def category_destinations(
    category: _format_config.FileCategory,
) -> tuple[str, str, str]:
    """Return the category, files, and paths namespace destinations."""
    prefix = _format_config._category_enable_prefix(category)
    files_prefix = _format_config._category_files_prefix(category)
    paths_prefix = _format_config._category_paths_prefix(category)
    return (
        _format_config.reduce_to_config_form(f"with_{prefix}"),
        _format_config.reduce_to_config_form(f"with_{files_prefix}_files"),
        _format_config.reduce_to_config_form(f"with_{paths_prefix}_paths"),
    )


class TestFormatConfig(unittest.TestCase):
    """Test file-format flags, resolution, and namespace validation."""

    def test_file_format_and_category_combinations(self) -> None:
        """Combined format and category flags should equal their component flags."""
        self.assertEqual(
            _format_config.FileFormat.SHOW_BOTH,
            _format_config.FileFormat.SHOW_CONTENTS
            | _format_config.FileFormat.SHOW_PATHS,
        )
        self.assertEqual(
            _format_config.FileFormat.SHOW_NONE, _format_config.FileFormat(0)
        )
        self.assertEqual(
            _format_config.FileCategory.ANY,
            _format_config.FileCategory.AUTHORS
            | _format_config.FileCategory.ATTRIBUTION
            | _format_config.FileCategory.NOTICES
            | _format_config.FileCategory.LEGACY
            | _format_config.FileCategory.OTHERS,
        )

    def test_split_categories_into_list(self) -> None:
        """Empty, unsupported, and combined category values should split correctly."""
        cases: tuple[tuple[_format_config.FileCategory, list], ...] = (
            (_format_config.FileCategory(0), []),
            (_format_config.FileCategory.METADATA, []),
            (
                _format_config.FileCategory.ATTRIBUTION
                | _format_config.FileCategory.AUTHORS,
                [
                    _format_config.FileCategory.ATTRIBUTION,
                    _format_config.FileCategory.AUTHORS,
                ],
            ),
            (
                _format_config.FileCategory.ANY,
                [
                    _format_config.FileCategory.ATTRIBUTION,
                    _format_config.FileCategory.AUTHORS,
                    _format_config.FileCategory.LEGACY,
                    _format_config.FileCategory.NOTICES,
                    _format_config.FileCategory.OTHERS,
                ],
            ),
        )

        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(
                    _format_config._split_categories_into_list(value),
                    expected,
                )

    def test_category_enable_prefix_maps_named_categories(self) -> None:
        """Each named category should map to its canonical enable prefix."""
        cases = (
            (_format_config.FileCategory.ATTRIBUTION, "attribution"),
            (_format_config.FileCategory.AUTHORS, "authors"),
            (_format_config.FileCategory.LEGACY, "legacy"),
            (_format_config.FileCategory.LICENSES, "license"),
            (_format_config.FileCategory.NOTICES, "notice"),
            (_format_config.FileCategory.OTHERS, "other"),
        )

        for category, expected in cases:
            with self.subTest(category=category):
                self.assertEqual(
                    _format_config._category_enable_prefix(category),
                    expected,
                )

    def test_category_enable_prefix_rejects_empty_and_unknown_categories(
        self,
    ) -> None:
        """Empty and unsupported category values should raise descriptive errors."""
        with self.assertRaisesRegex(TypeError, "non-empty"):
            _format_config._category_enable_prefix(
                _format_config.FileCategory(0)
            )

        with self.assertRaisesRegex(ValueError, "unique FileCategory"):
            _format_config._category_enable_prefix(
                _format_config.FileCategory.METADATA
            )

    def test_category_files_and_paths_prefixes(self) -> None:
        """Files and paths helpers should return each category's canonical prefix."""
        cases = (
            (_format_config.FileCategory.ATTRIBUTION, "attribution"),
            (_format_config.FileCategory.AUTHORS, "authors"),
            (_format_config.FileCategory.LEGACY, "legacy"),
            (_format_config.FileCategory.LICENSES, "license"),
            (_format_config.FileCategory.NOTICES, "notice"),
            (_format_config.FileCategory.OTHERS, "other"),
        )

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
        """Empty and unnamed category values should be rejected."""
        with self.assertRaisesRegex(ValueError, "non-empty"):
            _format_config._category_files_prefix(
                _format_config.FileCategory(0)
            )
        # Rationale: error message behavior differs if <=3.10;
        with self.assertRaisesRegex(
            ValueError,
            "is not a valid"
            if sys.version_info < (3, 11)
            else "invalid value",
        ):
            _format_config._category_files_prefix(
                _format_config.FileCategory(128)
            )

    def test_effective_bool_resolves_values_and_defaults(self) -> None:
        """Namespace values should resolve to tri-state booleans or the given default."""
        cases = (
            (Namespace(), "missing", None, None),
            (Namespace(), "missing", True, True),
            (Namespace(value=None), "value", False, False),
            (Namespace(value=True), "value", None, True),
            (Namespace(value=False), "value", None, False),
            (Namespace(value=1), "value", None, True),
            (Namespace(value=""), "value", None, False),
        )

        for args, dest, default, expected in cases:
            with self.subTest(dest=dest, value=getattr(args, dest, None)):
                self.assertIs(
                    _format_config._effective_bool(
                        args, dest, default=default
                    ),
                    expected,
                )

    def test_tri_state_and_global_state_helpers(self) -> None:
        """Deprecated and global state helpers should preserve tri-state values."""
        args = Namespace(
            tri=None,
            with_files=True,
            with_paths=False,
        )

        self.assertIsNone(_format_config._tri_state(args, "tri"))
        self.assertIsNone(_format_config._tri_state(args, "missing"))
        self.assertIs(_format_config._global_files_state(args), True)
        self.assertIs(_format_config._global_paths_state(args), False)
        self.assertIsNone(_format_config._global_files_state(Namespace()))
        self.assertIsNone(_format_config._global_paths_state(Namespace()))

    def test_category_state_precedence_and_file_path_states(self) -> None:
        """Category, files, and paths helpers should resolve precedence and defaults."""
        category = _format_config.FileCategory.AUTHORS
        category_dest, files_dest, paths_dest = category_destinations(category)

        args = Namespace(
            **{
                category_dest: None,
                files_dest: False,
                paths_dest: True,
            }
        )
        self.assertIs(_format_config._category_state(args, category), False)
        self.assertIs(
            _format_config._category_files_state(args, category), False
        )
        self.assertIs(
            _format_config._category_paths_state(args, category), True
        )

        args = Namespace(
            **{
                category_dest: None,
                files_dest: None,
                paths_dest: True,
            }
        )
        self.assertIs(_format_config._category_state(args, category), True)

        args = Namespace(
            **{
                category_dest: True,
                files_dest: False,
                paths_dest: None,
            }
        )
        self.assertIs(_format_config._category_state(args, category), True)

        license_category = _format_config.FileCategory.LICENSES
        license_dest, license_files_dest, license_paths_dest = (
            category_destinations(license_category)
        )
        args = Namespace(
            **{
                license_dest: None,
                license_files_dest: None,
                license_paths_dest: None,
            }
        )
        self.assertIs(
            _format_config._category_state(args, license_category), True
        )

        args = Namespace(
            **{
                category_dest: None,
                files_dest: None,
                paths_dest: None,
            }
        )
        self.assertIsNone(_format_config._category_state(args, category))
        self.assertIsNone(_format_config._category_files_state(args, category))
        self.assertIsNone(_format_config._category_paths_state(args, category))

    def test_summary_active(self) -> None:
        """Summary mode should be active only when its value resolves to true."""
        cases = (
            (None, False),
            (False, False),
            (True, True),
            (1, True),
        )

        for summary, expected in cases:
            with self.subTest(summary=summary):
                self.assertIs(
                    _format_config._summary_active(Namespace(summary=summary)),
                    expected,
                )

    def test_resolve_file_format_uses_none_as_the_default(self) -> None:
        """Unspecified formats should be off; explicit legacy file/path flags should resolve."""
        self.assertEqual(
            _format_config.resolve_file_format(Namespace()),
            _format_config.FileFormat.SHOW_NONE,
        )
        self.assertEqual(
            _format_config.resolve_file_format(
                Namespace(with_legacy_files=True)
            ),
            _format_config.FileFormat.SHOW_CONTENTS,
        )
        self.assertEqual(
            _format_config.resolve_file_format(
                Namespace(with_legacy_paths=True)
            ),
            _format_config.FileFormat.SHOW_PATHS,
        )

    def test_resolve_file_formats_returns_each_format_category(self) -> None:
        """Resolution should include every format-able category."""
        formats = _format_config.resolve_file_formats(Namespace())

        self.assertEqual(set(formats), set(CATEGORIES))
        self.assertTrue(
            all(
                value == _format_config.FileFormat.SHOW_NONE
                for value in formats.values()
            )
        )

    def test_apply_effective_bit_applies_tristate_settings_independently(
        self,
    ) -> None:
        """File and path settings should independently preserve, enable, or disable bits."""
        cases = (
            (None, None, (False, False)),
            (True, None, (True, False)),
            (None, True, (False, True)),
            (False, True, (False, True)),
            (True, False, (True, False)),
        )

        for files, paths, expected in cases:
            with self.subTest(files=files, paths=paths):
                self.assertEqual(
                    _format_config._apply_effective_bit(
                        current_files=False,
                        current_paths=False,
                        files_setting=files,
                        paths_setting=paths,
                    ),
                    expected,
                )

    def test_apply_single_flag_applies_selected_format_bits(self) -> None:
        """A tri-state flag should no-op, enable, or disable only selected bits."""
        cases = (
            (
                _format_config.FileFormat.SHOW_NONE,
                None,
                True,
                True,
                _format_config.FileFormat.SHOW_NONE,
            ),
            (
                _format_config.FileFormat.SHOW_NONE,
                True,
                True,
                False,
                _format_config.FileFormat.SHOW_CONTENTS,
            ),
            (
                _format_config.FileFormat.SHOW_NONE,
                True,
                False,
                True,
                _format_config.FileFormat.SHOW_PATHS,
            ),
            (
                _format_config.FileFormat.SHOW_NONE,
                True,
                True,
                True,
                _format_config.FileFormat.SHOW_BOTH,
            ),
            (
                _format_config.FileFormat.SHOW_BOTH,
                False,
                True,
                False,
                _format_config.FileFormat.SHOW_PATHS,
            ),
            (
                _format_config.FileFormat.SHOW_BOTH,
                False,
                False,
                True,
                _format_config.FileFormat.SHOW_CONTENTS,
            ),
            (
                _format_config.FileFormat.SHOW_BOTH,
                False,
                True,
                True,
                _format_config.FileFormat.SHOW_NONE,
            ),
        )

        for current, value, show_files, show_paths, expected in cases:
            with self.subTest(
                current=current,
                value=value,
                show_files=show_files,
                show_paths=show_paths,
            ):
                self.assertEqual(
                    _format_config._apply_single_flag(
                        current,
                        value=value,
                        show_files=show_files,
                        show_paths=show_paths,
                    ),
                    expected,
                )

    def test_resolve_category_output_bits_obeys_precedence(self) -> None:
        """Output bits should follow category state, local overrides, then global fallback."""
        category = _format_config.FileCategory.LEGACY
        category_dest, files_dest, paths_dest = category_destinations(category)

        self.assertEqual(
            _format_config._resolve_category_output_bits(
                Namespace(
                    **{
                        category_dest: False,
                        files_dest: True,
                        paths_dest: True,
                    }
                ),
                category,
            ),
            (False, False),
        )

        self.assertEqual(
            _format_config._resolve_category_output_bits(
                Namespace(
                    **{
                        category_dest: True,
                        files_dest: False,
                        paths_dest: None,
                    }
                ),
                category,
            ),
            (False, True),
        )

        self.assertEqual(
            _format_config._resolve_category_output_bits(
                Namespace(with_files=True, with_paths=False),
                category,
            ),
            (True, False),
        )

        self.assertEqual(
            _format_config._resolve_category_output_bits(
                Namespace(), category
            ),
            (False, False),
        )

    def test_resolve_category_format_exercises_each_category_rule(
        self,
    ) -> None:
        """Each category's format rules should return a valid format for tri-state values."""
        flag_destinations = {
            "summary": None,
            "global_files": None,
            "global_paths": None,
            "with_license_file": None,
            "with_license_files": None,
            "with_license_paths": None,
            "with_licenses": None,
            "with_others": None,
            "with_other_files": None,
            "with_other_paths": None,
            "with_attribution": None,
            "with_attribution_files": None,
            "with_attribution_paths": None,
            "with_authors_files": None,
            "with_authors_paths": None,
            "with_notices": None,
            "with_notice_files": None,
            "with_notice_paths": None,
            "with_legacy": None,
            "with_legacy_files": None,
            "with_legacy_paths": None,
        }
        tri_state_values = (None, True, False)
        valid_formats = (
            _format_config.FileFormat.SHOW_NONE,
            _format_config.FileFormat.SHOW_CONTENTS,
            _format_config.FileFormat.SHOW_PATHS,
            _format_config.FileFormat.SHOW_BOTH,
        )

        for category in CATEGORIES:
            for flag_value in tri_state_values:
                with self.subTest(category=category, flag_value=flag_value):
                    args = Namespace(
                        **dict.fromkeys(flag_destinations, flag_value)
                    )
                    result = _format_config._resolve_category_format(
                        args,
                        category=category,
                        default=_format_config.FileFormat.SHOW_BOTH,
                    )
                    self.assertIn(result, valid_formats)

    def test_resolve_category_format_rejects_unsupported_categories(
        self,
    ) -> None:
        """Aggregate and unnamed categories should raise ValueError."""
        for category in (
            _format_config.FileCategory.METADATA,
            _format_config.FileCategory.ANY,
        ):
            with (
                self.subTest(category=category),
                self.assertRaisesRegex(
                    ValueError,
                    "Unsupported file category",
                ),
            ):
                _format_config._resolve_category_format(
                    Namespace(),
                    category=category,
                )

        # Rationale: error message behavior differs if <=3.10;
        with self.assertRaisesRegex(
            ValueError,
            "is not a valid"
            if sys.version_info < (3, 11)
            else "invalid value",
        ):
            _format_config._resolve_category_format(
                Namespace(),
                category=_format_config.FileCategory(128),
            )

    def test_resolve_file_format_legacy_defaults_and_overrides(self) -> None:
        """Legacy resolution should handle defaults and global files/paths settings."""
        self.assertEqual(
            _format_config.resolve_file_format_legacy(Namespace()),
            _format_config.FileFormat.SHOW_NONE,
        )
        self.assertEqual(
            _format_config.resolve_file_format_legacy(
                Namespace(with_files=True)
            ),
            _format_config.FileFormat.SHOW_CONTENTS,
        )
        self.assertEqual(
            _format_config.resolve_file_format_legacy(
                Namespace(with_paths=True)
            ),
            _format_config.FileFormat.SHOW_PATHS,
        )
        self.assertEqual(
            _format_config.resolve_file_format_legacy(
                Namespace(with_files=True, with_paths=True)
            ),
            _format_config.FileFormat.SHOW_BOTH,
        )
        self.assertEqual(
            _format_config.resolve_file_format_legacy(Namespace(summary=True)),
            _format_config.FileFormat.SHOW_NONE,
        )

    def test_resolve_file_format_legacy_rejects_conflicting_state(
        self,
    ) -> None:
        """Summary and category conflicts should raise AttributeError."""
        category = _format_config.FileCategory.LEGACY
        category_dest, files_dest, _ = category_destinations(category)

        with self.assertRaisesRegex(
            AttributeError,
            "Conflicting flags for mode",
        ):
            _format_config.resolve_file_format_legacy(
                Namespace(summary=True, **{files_dest: True})
            )

        with self.assertRaisesRegex(AttributeError, "Conflicting flags for"):
            _format_config.resolve_file_format_legacy(
                Namespace(**{category_dest: True})
            )

        try:
            _format_config.resolve_file_format_legacy(
                Namespace(summary=True, **{files_dest: True})
            )
        except AttributeError as error:
            self.assertIsNotNone(error.__cause__)
            self.assertIsInstance(error.__cause__, ValueError)
            self.assertIn("both set", str(error.__cause__))
        else:
            self.fail("Expected conflicting state to raise AttributeError")

    def test_resolve_file_format_legacy_rejects_unnamed_category(self) -> None:
        """Legacy resolution should reject unnamed categories."""
        with self.assertRaisesRegex(ValueError, "Only supported"):
            _format_config.resolve_file_format_legacy(
                Namespace(),
                category=_format_config.FileCategory(0),
            )
        # Rationale: error message behavior differs if <=3.10;
        with self.assertRaisesRegex(
            ValueError,
            "is not a valid"
            if sys.version_info < (3, 11)
            else "invalid value",
        ):
            _format_config.resolve_file_format_legacy(
                Namespace(),
                category=_format_config.FileCategory(128),
            )

    def test_validate_namespace_summary_short_circuits(self) -> None:
        """Summary mode should bypass normal namespace validation."""
        parser = Mock(spec=ArgumentParser)

        _format_config.validate_file_format_namespace(
            parser,
            Namespace(summary=True),
        )

        parser.error.assert_not_called()

    def test_validate_namespace_rejects_category_conflicts(self) -> None:
        """A disabled category should reject enabled category-local files or paths."""
        category_dest, files_dest, paths_dest = category_destinations(
            _format_config.FileCategory.LEGACY
        )
        cases = (
            (True, None),
            (False, True),
        )

        for files, paths in cases:
            with self.subTest(files=files, paths=paths):
                parser = Mock(spec=ArgumentParser)
                parser.error.side_effect = SystemExit(2)
                args = Namespace(
                    **{
                        category_dest: False,
                        files_dest: files,
                        paths_dest: paths,
                    }
                )

                with self.assertRaises(SystemExit):
                    _format_config.validate_file_format_namespace(parser, args)

                error_message = parser.error.call_args.args[0]
                self.assertIn("Conflicting flags for legacy", error_message)
                self.assertIn("--without-legacy", error_message)

    def test_validate_namespace_rejects_global_enable_without_active_categories(
        self,
    ) -> None:
        """Global file or path enablement should fail when no category is active."""
        cases = (
            (True, None),
            (None, True),
        )

        for global_files, global_paths in cases:
            with self.subTest(
                global_files=global_files,
                global_paths=global_paths,
            ):
                parser = Mock(spec=ArgumentParser)
                parser.error.side_effect = SystemExit(2)

                with self.assertRaises(SystemExit):
                    _format_config.validate_file_format_namespace(
                        parser,
                        Namespace(
                            with_files=global_files,
                            with_paths=global_paths,
                        ),
                    )

                self.assertIn(
                    "requires at least one active category",
                    parser.error.call_args.args[0],
                )

    def test_validate_namespace_accepts_category_overrides(self) -> None:
        """An enabled category may validly disable one local output format."""
        category_dest, files_dest, paths_dest = category_destinations(
            _format_config.FileCategory.LEGACY
        )
        parser = Mock(spec=ArgumentParser)

        _format_config.validate_file_format_namespace(
            parser,
            Namespace(
                **{
                    category_dest: True,
                    files_dest: False,
                    paths_dest: True,
                }
            ),
        )

        parser.error.assert_not_called()

    def test_validate_namespace_accepts_global_enable_with_active_category(
        self,
    ) -> None:
        """Global file enablement should succeed when a license-file category is active."""
        parser = Mock(spec=ArgumentParser)

        _format_config.validate_file_format_namespace(
            parser,
            Namespace(
                with_files=True,
                with_license_files=True,
            ),
        )

        parser.error.assert_not_called()

    def test_resolve_file_format_legacy_disabled_category_with_paths_override(
        self,
    ) -> None:
        """A local paths setting should determine output even when the category is disabled."""
        category_dest, _, paths_dest = category_destinations(
            _format_config.FileCategory.LEGACY
        )

        cases = (
            (True, _format_config.FileFormat.SHOW_PATHS),
            (False, _format_config.FileFormat.SHOW_NONE),
        )

        for paths_enabled, expected in cases:
            with self.subTest(paths_enabled=paths_enabled):
                self.assertEqual(
                    _format_config.resolve_file_format_legacy(
                        Namespace(
                            **{
                                category_dest: False,
                                paths_dest: paths_enabled,
                            }
                        )
                    ),
                    expected,
                )


if __name__ == "__main__":
    # Run tests with unittest
    unittest.main(verbosity=2)
