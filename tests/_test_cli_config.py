# tests._test_cli_config
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


"""Unit tests for piplicenses.cli.config using only stdlib unittest."""

import warnings
from argparse import Namespace

# now import patch from unittest
from unittest.mock import patch

# now import test fixtures
from piplicenses import __version__
from piplicenses.cli import config

from . import unittest


class SplitLegacyTokensTests(unittest.TestCase):
    def test_splits_plain_and_trailing_tokens(self) -> None:
        self.assertEqual(config._split_legacy_tokens("a;b;c"), ["a", "b", "c"])
        self.assertEqual(
            config._split_legacy_tokens("a;b;c;"), ["a", "b", "c"]
        )
        self.assertEqual(config._split_legacy_tokens(""), [""])

    def test_preserves_escaped_tokens_and_backslashes(self) -> None:
        self.assertEqual(config._split_legacy_tokens(r"a\;b;c"), ["a;b", "c"])
        self.assertEqual(config._split_legacy_tokens(r"a\\b;c"), [r"a\b", "c"])

    def test_preserves_unrecognized_escape(self) -> None:
        self.assertEqual(config._split_legacy_tokens(r"a\q;b"), [r"a\q", "b"])

    def test_rejects_empty_token(self) -> None:
        with (
            patch.object(config, "LEGACY_TOKEN", ""),
            self.assertRaisesRegex(ValueError, "must be non-empty"),
        ):
            config._split_legacy_tokens("value")

    def test_rejects_token_containing_backslash(self) -> None:
        with (
            patch.object(config, "LEGACY_TOKEN", r"\;"),
            self.assertRaisesRegex(ValueError, "must not contain"),
        ):
            config._split_legacy_tokens("value")


class SerializationHelpersTests(unittest.TestCase):
    def test_serialize_input_str_handles_strings_bytes_and_other_values(
        self,
    ) -> None:
        self.assertEqual(config._serialize_input_str("text"), "text")
        self.assertEqual(config._serialize_input_str(b"text"), "text")
        self.assertIsNone(config._serialize_input_str(None))
        self.assertIsNone(config._serialize_input_str(42))  # type: ignore[arg-type]

    def test_parse_serialized_handles_empty_and_single_values(self) -> None:
        self.assertEqual(config._parse_serialized(""), set())
        self.assertEqual(config._parse_serialized("   "), set())
        self.assertEqual(
            config._parse_serialized("  BSD-2-Clause  "), {"BSD-2-Clause"}
        )

    def test_parse_serialized_splits_and_discards_empty_tokens(self) -> None:
        self.assertEqual(
            config._parse_serialized(" BSD-2-Clause ; ; MIT License ; "),
            {"BSD-2-Clause", "MIT License"},
        )

    def test_parse_serialized_preserves_escaped_token(self) -> None:
        self.assertEqual(
            config._parse_serialized(
                r"BSD-2-Clause\;MIT License;Python Software Foundation License"
            ),
            {"BSD-2-Clause;MIT License", "Python Software Foundation License"},
        )

    def test_normalize_as_set_accepts_none_strings_and_bytes(self) -> None:
        self.assertEqual(config._normalize_as_set(None), set())
        self.assertEqual(
            config._normalize_as_set("BSD-2-Clause;MIT License"),
            {"BSD-2-Clause", "MIT License"},
        )
        self.assertEqual(
            config._normalize_as_set(b"BSD-2-Clause;MIT License"),
            {"BSD-2-Clause", "MIT License"},
        )
        self.assertEqual(config._normalize_as_set(b""), set())

    def test_normalize_as_set_flattens_iterables_and_skips_empty_items(
        self,
    ) -> None:
        value = [
            "BSD-3-Clause",
            None,
            " MIT License ; Python Software Foundation License ",
            b"pip;packages",
            "",
            "   ",
            ";",
            42,
            [
                "Apache-2.0 OR BSD-2-Clause",
                None,
                "BSD-2-Clause;Mozilla Public License 2.0 (MPL 2.0)",
            ],
            {"alpha", "beta"},
        ]
        self.assertEqual(
            config._normalize_as_set(value),
            {
                "BSD-3-Clause",
                "MIT License",
                "Python Software Foundation License",
                "pip",
                "packages",
                "42",
                "Apache-2.0 OR BSD-2-Clause",
                "BSD-2-Clause",
                "Mozilla Public License 2.0 (MPL 2.0)",
                "alpha",
                "beta",
            },
        )

    def test_normalize_as_set_best_effort_for_non_iterable(self) -> None:
        self.assertEqual(config._normalize_as_set(42), {"42"})  # type: ignore[arg-type]
        self.assertEqual(config._normalize_as_set(0), {"0"})  # type: ignore[arg-type]

    def test_serialize_to_semi_str_is_sorted_and_round_trips(self) -> None:
        values = {"MIT License", "BSD-2-Clause", "a;b", r"c:\path"}
        serialized = config._serialize_to_semi_str(values)
        self.assertEqual(serialized, config._serialize_to_semi_str(values))
        self.assertIn(r"a\;b", serialized)
        self.assertEqual(config._normalize_as_set(serialized), values)

    def test_serialize_to_semi_str_handles_string_empty_and_whitespace(
        self,
    ) -> None:
        self.assertEqual(config._serialize_to_semi_str(set()), ";")
        self.assertEqual(
            config._serialize_to_semi_str("  BSD-2-Clause  "), "BSD-2-Clause"
        )
        self.assertEqual(
            config._serialize_to_semi_str({" leading ", "trailing "}),
            "leading;trailing",
        )


class SetOfStrTests(unittest.TestCase):
    def test_descriptor_class_access_and_default_value(self) -> None:
        class Example:
            values = config.SetOfStr()

        self.assertIsInstance(Example.values, config.SetOfStr)
        self.assertEqual(Example().values, set())

    def test_descriptor_normalizes_assignment_and_deletion(self) -> None:
        class Example:
            values = config.SetOfStr("initial-name")

        example = Example()
        example.values = "BSD-2-Clause;MIT License"
        self.assertEqual(example.values, {"BSD-2-Clause", "MIT License"})

        example.values = None
        self.assertEqual(example.values, set())

        del example.values
        self.assertEqual(example.values, set())

        # Deleting an absent descriptor-backed attribute is safe as well.
        del example.values
        self.assertEqual(example.values, set())


class ConfigurationTests(unittest.TestCase):
    def test_defaults_and_per_instance_sets(self) -> None:
        first = config.Configuration()
        second = config.Configuration()

        self.assertEqual(first.ignore_packages, set())
        self.assertEqual(first.packages, set())
        self.assertEqual(first.allow_packages, set())
        self.assertEqual(first.warn_on, set())
        self.assertEqual(first.fail_on, set())
        self.assertEqual(first.allow_only, set())

        first.packages.add("one")
        self.assertEqual(second.packages, set())

    def test_post_init_normalizes_iterables_and_preserves_none(self) -> None:
        """Test post-init runtime behavior converges on optional set types."""
        conf = config.Configuration(
            ignore_packages=[  # type: ignore[arg-type]
                "BSD-2-Clause",
                "MIT License;Python Software Foundation License",
            ],
            packages=("pip", "packages"),  # type: ignore[arg-type]
            fail_on=["license"],  # type: ignore[arg-type]
            allow_only=["approved"],  # type: ignore[arg-type]
            allow_packages=["allowed"],  # type: ignore[arg-type]
            warn_on=["warning"],  # type: ignore[arg-type]
        )
        self.assertEqual(
            conf.ignore_packages,
            {
                "BSD-2-Clause",
                "MIT License",
                "Python Software Foundation License",
            },
        )
        self.assertEqual(conf.packages, {"pip", "packages"})
        self.assertEqual(conf.fail_on, {"license"})
        self.assertEqual(conf.allow_only, {"approved"})
        self.assertEqual(conf.allow_packages, {"allowed"})
        self.assertEqual(conf.warn_on, {"warning"})

        conf_with_none = config.Configuration(
            ignore_packages=None,  # type: ignore[arg-type]
            packages=None,  # type: ignore[arg-type]
            fail_on=None,
            allow_only=None,
            allow_packages=None,  # type: ignore[arg-type]
            warn_on=None,  # type: ignore[arg-type]
        )
        self.assertEqual(conf_with_none.ignore_packages, set())
        self.assertEqual(conf_with_none.packages, set())
        self.assertIsNone(conf_with_none.fail_on)
        self.assertIsNone(conf_with_none.allow_only)
        self.assertEqual(conf_with_none.allow_packages, set())
        self.assertIsNone(conf_with_none.warn_on)

    def test_normalize_and_serialize_static_helpers(self) -> None:
        self.assertEqual(config.Configuration._normalize_to_set(None), set())
        self.assertEqual(
            config.Configuration._normalize_to_set("BSD-2-Clause;MIT License"),
            {"BSD-2-Clause", "MIT License"},
        )
        self.assertEqual(
            config.Configuration._serialize_to_semi_str(None),
            "",
        )
        self.assertEqual(
            config.Configuration._serialize_to_semi_str(
                {"MIT License", "BSD-2-Clause"}
            ),
            "BSD-2-Clause;MIT License",
        )

    def test_from_namespace_and_to_namespace(self) -> None:
        ns = Namespace(summary=True, packages=["BSD-2-Clause;MIT License"])
        conf = config.Configuration.from_namespace(ns)

        self.assertTrue(conf.summary)
        self.assertEqual(conf.packages, {"BSD-2-Clause", "MIT License"})

        converted = conf.to_namespace()
        self.assertIsInstance(converted, Namespace)
        self.assertEqual(vars(converted), vars(conf))

    def test_substitute_attr_aliases_and_fallback(self) -> None:
        conf = config.Configuration()

        self.assertEqual(
            conf.__substitute_attr__("  IGNORE_PACKAGES "), "ignore_packages"
        )
        self.assertEqual(conf.__substitute_attr__("fail_on_str"), "fail_on")
        self.assertEqual(
            conf.__substitute_attr__("allow_only_str"), "allow_only"
        )
        self.assertEqual(
            conf.__substitute_attr__("with_license"), "with_licenses"
        )
        self.assertEqual(conf.__substitute_attr__("unknown"), "unknown")

        with self.assertRaises(AttributeError):
            conf.__substitute_attr__(None)  # type: ignore[arg-type]

    def test_substitute_attr_legacy_warning_branch(self) -> None:
        conf = config.Configuration()

        # The warning path is enabled for non-6.0 versions and uses the
        # three-name no-version alias mapping.
        with (
            patch.object(config, "__version__", "6.1.0"),
            patch.object(config, "warnings", warnings, create=True),
            warnings.catch_warnings(record=True) as caught,
        ):
            warnings.simplefilter("always")
            self.assertEqual(
                conf.__substitute_attr__("no_version"), "without_versions"
            )

        self.assertTrue(caught)
        self.assertIsInstance(caught[0].message, Warning)

        with patch.object(config, "__version__", "6.0.0"):
            self.assertEqual(
                conf.__substitute_attr__("no_version"), "without_versions"
            )

    def test_getattr_boolean_set_inversion_and_generic_fallbacks(self) -> None:
        conf = config.Configuration()

        self.assertFalse(conf.__getattr__("summary"))
        self.assertIsNone(conf.__getattr__("with_license"))
        self.assertTrue(conf.with_licenses)
        self.assertEqual(conf.__getattr__("packages"), set())
        self.assertIsNone(conf.__getattr__("unrecognized_attribute"))

        with self.assertRaises(AttributeError):
            conf.__getattr__("__special__")

    def test_getattr_v6_0_notice_paths_fallback(self) -> None:
        conf = config.Configuration()

        with patch.object(config, "__version__", "6.0.0"):
            self.assertTrue(conf.__getattr__("with_notice_paths"))

        with patch.object(config, "__version__", "6.1.0"):
            self.assertFalse(conf.__getattr__("with_notice_paths"))

    def test_apply_updates_values_and_returns_configuration(self) -> None:
        conf = config.Configuration()
        result = conf.apply(summary=True, output_file="report.txt")

        self.assertIs(result, conf)
        self.assertTrue(conf.summary)
        self.assertEqual(conf.output_file, "report.txt")

    def test_apply_rejects_dunder_unknown_key(self) -> None:
        conf = config.Configuration()

        with self.assertRaisesRegex(
            AttributeError,
            "Unknown configuration key: __unknown__",
        ):
            conf.apply(**{"__unknown__": True})  # noqa: PIE804 -- tests runtime behavior

    def test_validate_is_a_no_op_fluent_method(self) -> None:
        conf = config.Configuration()
        self.assertIs(conf.validate(), conf)

    def test_read_tristate_and_coalesce_bool(self) -> None:
        class Values:
            missing = None
            false_value = False
            true_value = True

        self.assertIsNone(
            config.Configuration._read_tristate(Values(), "missing")
        )
        self.assertIs(
            config.Configuration._read_tristate(
                Values(), "not_present", "missing", "true_value"
            ),
            True,
        )
        self.assertIs(
            config.Configuration._read_tristate(
                Values(), "false_value", "true_value"
            ),
            False,
        )
        self.assertIsNone(config.Configuration._coalesce_bool(None, None))
        self.assertIs(
            config.Configuration._coalesce_bool(None, False, True), False
        )
        self.assertIs(config.Configuration._coalesce_bool(True, False), True)

    def test_set_properties_copy_and_normalize_values(self) -> None:
        conf = config.Configuration()

        properties = (
            ("ignore_packages_set", "ignore_packages"),
            ("packages_set", "packages"),
            ("allow_packages_set", "allow_packages"),
            ("allow_only_set", "allow_only"),
            ("fail_on_set", "fail_on"),
        )
        for property_name, backing_name in properties:
            with self.subTest(property_name=property_name):
                setattr(conf, property_name, ["BSD-2-Clause;MIT License"])
                self.assertEqual(
                    getattr(conf, property_name),
                    {"BSD-2-Clause", "MIT License"},
                )
                self.assertEqual(
                    getattr(conf, backing_name),
                    {"BSD-2-Clause", "MIT License"},
                )

                # Accessors return a copy, not the mutable backing set.
                returned = getattr(conf, property_name)
                returned.add("external")
                self.assertNotIn("external", getattr(conf, backing_name))

                setattr(conf, property_name, None)
                self.assertEqual(getattr(conf, property_name), set())

    def test_without_path_properties_invert_only_false(self) -> None:
        conf = config.Configuration()

        path_properties = (
            ("without_license_paths", "with_license_paths"),
            ("without_notice_paths", "with_notice_paths"),
            ("without_other_paths", "with_other_paths"),
        )
        for property_name, inverse_name in path_properties:
            with self.subTest(property_name=property_name):
                # test setting inverse
                setattr(conf, inverse_name, False)
                # should be true
                self.assertTrue(getattr(conf, property_name))
                # test setting direct
                setattr(conf, property_name, True)
                # still false
                self.assertFalse(getattr(conf, inverse_name))
                # still true
                self.assertTrue(getattr(conf, property_name))
                # now try unsetting too
                setattr(conf, property_name, None)
                # should still be false
                self.assertFalse(getattr(conf, inverse_name))
                # should still be true
                self.assertTrue(getattr(conf, property_name))

    def test_without_path_propertie_invert_mixed_false(self) -> None:
        conf = config.Configuration()

        path_properties = (("without_file_paths", "global_paths"),)
        for property_name, inverse_name in path_properties:
            with self.subTest(property_name=property_name):
                # test setting inverse
                setattr(conf, inverse_name, False)
                # should be true
                self.assertTrue(getattr(conf, property_name))
                # test setting direct
                setattr(conf, property_name, True)
                # still false
                self.assertFalse(getattr(conf, inverse_name))
                # still true
                self.assertTrue(getattr(conf, property_name))
                # now try unsetting too
                setattr(conf, property_name, None)
                # should still be false
                self.assertFalse(getattr(conf, inverse_name))
                # should no-longer be true (special case)
                self.assertFalse(getattr(conf, property_name))

    def test_v6_1_deprecated_properties_warn_and_update_canonical_fields(
        self,
    ) -> None:
        conf = config.Configuration()

        # These properties are defined only in the v6.1 class-definition branch.
        deprecated_names = (
            "no_version",
            "no_file_paths",
            "no_license_path",
            "with_description",
            "with_notice_file",
            "with_license_file",
        )
        if not all(
            name in config.Configuration.__dict__ for name in deprecated_names
        ):
            self.skipTest(
                "Deprecated properties are not present in this version"
            )

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            conf.no_version = True
            self.assertTrue(conf.no_version)

            conf.no_file_paths = True
            self.assertFalse(conf.global_paths)
            # test actual runtime behavior (this may change in v6.1 True->None)
            conf.no_file_paths = None  # type: ignore[assignment]
            self.assertTrue(conf.global_paths)
            conf.no_file_paths = False
            self.assertTrue(conf.global_paths)

            conf.no_license_path = True
            self.assertTrue(conf.without_license_paths)

            conf.with_description = True
            self.assertTrue(conf.with_descriptions)
            conf.with_notice_file = True
            self.assertTrue(
                conf.with_notice_files
                if "6.1" in __version__
                else conf.with_notice_file,
            )
            conf.with_license_file = True
            self.assertTrue(
                conf.with_license_files
                if "6.1" in __version__
                else conf.with_license_file,
            )

        self.assertGreaterEqual(len(caught), len(list(deprecated_names)) - 1)
        self.assertTrue(
            all(isinstance(item.message, Warning) for item in caught)
        )

    def test_v6_0_deprecated_serialized_properties_when_defined(self) -> None:
        conf = config.Configuration()
        deprecated_names = ("allow_only_str", "fail_on_str")
        if not all(
            name in config.Configuration.__dict__ for name in deprecated_names
        ):
            self.skipTest(
                "v6.0 deprecated properties are not present in this version"
            )

        conf.allow_only_str = "BSD-2-Clause;MIT License"
        conf.fail_on_str = ["license", "notice"]
        self.assertEqual(conf.allow_only, {"BSD-2-Clause", "MIT License"})
        self.assertEqual(conf.fail_on, {"license", "notice"})
        self.assertEqual(conf.allow_only_str, "BSD-2-Clause;MIT License")
        self.assertEqual(conf.fail_on_str, "license;notice")

    def test_v6_0_compatibility_properties_when_defined(self) -> None:
        conf = config.Configuration()
        deprecated_names = (
            "with_system",
            "without_file_paths",
            "no_license_path",
            "with_descriptions",
        )
        if not all(
            name in config.Configuration.__dict__ for name in deprecated_names
        ):
            self.skipTest(
                "v6.0 compatibility properties are not present in this version"
            )

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            conf.with_system = True
            self.assertTrue(conf.with_system)
            self.assertTrue(conf.include_from_system)
            self.assertEqual(conf.with_system, conf.include_from_system)
            # default pair (with == None, without == not True)
            self.assertIsNone(conf.with_file_paths)
            self.assertFalse(conf.without_file_paths)

            conf.no_license_path = True
            self.assertFalse(conf.with_license_paths)

            conf.with_descriptions = True
            self.assertTrue(conf.with_description)

        self.assertTrue(caught)
        self.assertTrue(
            all(isinstance(item.message, Warning) for item in caught)
        )


__all__ = [
    """ConfigurationTests""",
    """SerializationHelpersTests""",
    """SetOfStrTests""",
    """SplitLegacyTokensTests""",
]


if __name__ == "__main__":
    # Run tests with unittest
    unittest.main(verbosity=2)
