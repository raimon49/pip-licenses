# -*- coding: utf-8 -*-
# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et
from __future__ import annotations

import copy
import email
import os
import re
import sys
import tempfile
import unittest
import venv
from enum import Enum, auto
from importlib.metadata import Distribution
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import docutils.frontend
import docutils.parsers.rst
import docutils.utils
import pytest
import tomli_w
from _pytest.capture import CaptureFixture

import piplicenses
from piplicenses import (
    DEFAULT_OUTPUT_FIELDS,
    LICENSE_UNKNOWN,
    SYSTEM_PACKAGES,
    CompatibleArgumentParser,
    FromArg,
    __pkgname__,
    case_insensitive_partial_match_set_diff,
    case_insensitive_partial_match_set_intersect,
    case_insensitive_set_diff,
    case_insensitive_set_intersect,
    create_licenses_table,
    create_output_string,
    create_parser,
    create_warn_string,
    enum_key_to_value,
    extract_homepage,
    factory_styled_table_with_args,
    find_license_from_classifier,
    get_output_fields,
    get_packages,
    get_sortby,
    normalize_pkg_name,
    normalize_version,
    normalize_pkg_name_and_version,
    output_colored,
    save_if_needs,
    select_license_by_source,
    value_to_enum_key,
)
from prettytable import HRuleStyle

if TYPE_CHECKING:
    if sys.version_info >= (3, 10):
        from importlib.metadata._meta import PackageMetadata
    else:
        from email.message import Message as PackageMetadata


UNICODE_APPENDIX = ""
with open("tests/fixtures/unicode_characters.txt", encoding="utf-8") as f:
    # Read from external file considering a terminal that cannot handle "emoji"
    UNICODE_APPENDIX = f.readline().replace("\n", "")


def importlib_metadata_distributions_mocked(
    *args: Any, **kwargs: Any
) -> list[Distribution]:
    class DistributionMocker(Distribution):
        def __init__(self, orig_dist: Distribution) -> None:
            self.__dist = orig_dist

        @property
        def metadata(self) -> PackageMetadata:
            return EmailMessageMocker(self.__dist.metadata)

    class EmailMessageMocker(email.message.Message):
        def __init__(self, orig_msg: PackageMetadata) -> None:
            self.__msg = orig_msg

        def __getattr__(self, attr: str) -> Any:
            return getattr(self.__msg, attr)

        def __getitem__(self, key: str) -> Any:
            if key.lower() == "name":
                return self.__msg["name"] + " " + UNICODE_APPENDIX
            return self.__msg[key]

    packages = list(importlib_metadata_distributions_orig(*args, **kwargs))
    packages[-1] = DistributionMocker(packages[-1])  # type: ignore[abstract]
    return packages


importlib_metadata_distributions_orig = (
    piplicenses.importlib_metadata.distributions
)


class CommandLineTestCase(unittest.TestCase):
    parser = create_parser()

    @classmethod
    def setUpClass(cls) -> None:
        cls.parser = create_parser()


class TestGetLicenses(CommandLineTestCase):
    def _create_pkg_name_columns(self, table):
        index = DEFAULT_OUTPUT_FIELDS.index("Name")

        # XXX: access to private API
        rows = copy.deepcopy(table.rows)
        pkg_name_columns = []
        for row in rows:
            pkg_name_columns.append(row[index])

        return pkg_name_columns

    def _create_license_columns(self, table, output_fields):
        index = output_fields.index("License")

        # XXX: access to private API
        rows = copy.deepcopy(table.rows)
        pkg_name_columns = []
        for row in rows:
            pkg_name_columns.append(row[index])

        return pkg_name_columns

    # from https://stackoverflow.com/questions/12883428/ ...
    # ... how-to-parse-restructuredtext-in-python
    @staticmethod
    def check_rst(text: str) -> None:
        parser = docutils.parsers.rst.Parser()
        components = (docutils.parsers.rst.Parser,)
        settings = docutils.frontend.OptionParser(
            components=components
        ).get_default_values()
        settings.halt_level = 3
        document = docutils.utils.new_document("<rst-doc>", settings=settings)
        parser.parse(text, document)

    def test_with_empty_args(self) -> None:
        empty_args: list[str] = []
        args = self.parser.parse_args(empty_args)
        table = create_licenses_table(args)

        self.assertIn("l", table.align.values())
        self.assertFalse(table.border)
        self.assertTrue(table.header)
        self.assertEqual("+", table.junction_char)
        self.assertEqual(HRuleStyle.FRAME, table.hrules)

        output_fields = get_output_fields(args)
        self.assertEqual(
            output_fields, list(DEFAULT_OUTPUT_FIELDS) + ["License"]
        )
        self.assertNotIn("Author", output_fields)
        self.assertNotIn("URL", output_fields)

        pkg_name_columns = self._create_pkg_name_columns(table)
        for sys_pkg in SYSTEM_PACKAGES:
            self.assertNotIn(sys_pkg, pkg_name_columns)

        sortby = get_sortby(args)
        self.assertEqual("Name", sortby)

        output_string = create_output_string(args)
        self.assertNotIn("<table>", output_string)

    def test_from_meta(self) -> None:
        from_args = ["--from=meta"]
        args = self.parser.parse_args(from_args)

        output_fields = get_output_fields(args)
        self.assertIn("License", output_fields)

        table = create_licenses_table(args, output_fields)
        license_columns = self._create_license_columns(table, output_fields)
        license_notation_as_meta = "MIT"
        self.assertIn(license_notation_as_meta, license_columns)

    def test_from_classifier(self) -> None:
        from_args = ["--from=classifier"]
        args = self.parser.parse_args(from_args)
        output_fields = get_output_fields(args)
        table = create_licenses_table(args, output_fields)

        self.assertIn("License", output_fields)

        license_columns = self._create_license_columns(table, output_fields)
        license_notation_as_classifier = "MIT License"
        self.assertIn(license_notation_as_classifier, license_columns)

    def test_from_mixed(self) -> None:
        from_args = ["--from=mixed"]
        args = self.parser.parse_args(from_args)
        output_fields = get_output_fields(args)
        table = create_licenses_table(args, output_fields)

        self.assertIn("License", output_fields)

        license_columns = self._create_license_columns(table, output_fields)
        # Depending on the condition "MIT" or "BSD" etc.
        license_notation_as_classifier = "MIT License"
        self.assertIn(license_notation_as_classifier, license_columns)

    def test_from_expression(self) -> None:
        from_args = ["--from=expression"]
        args = self.parser.parse_args(from_args)
        output_fields = get_output_fields(args)
        table = create_licenses_table(args, output_fields)

        self.assertIn("License", output_fields)

        license_columns = self._create_license_columns(table, output_fields)
        license_notation_as_expression = "MIT"
        # TODO enable assert once a dependency uses 'License-Expression'
        # TODO (maybe black)
        # self.assertIn(license_notation_as_expression, license_columns)

    def test_from_all(self) -> None:
        from_args = ["--from=all"]
        args = self.parser.parse_args(from_args)
        output_fields = get_output_fields(args)
        table = create_licenses_table(args, output_fields)

        self.assertIn("License-Metadata", output_fields)
        self.assertIn("License-Classifier", output_fields)
        self.assertIn("License-Expression", output_fields)

        index_license_meta = output_fields.index("License-Metadata")
        license_meta = []
        for row in table.rows:
            license_meta.append(row[index_license_meta])

        index_license_classifier = output_fields.index("License-Classifier")
        license_classifier = []
        for row in table.rows:
            license_classifier.append(row[index_license_classifier])

        index_license_expression = output_fields.index("License-Expression")
        license_expression = [
            row[index_license_expression] for row in table.rows
        ]

        for license_name in ("BSD", "MIT", "Apache 2.0"):
            self.assertIn(license_name, license_meta)
        for license_name in (
            "BSD License",
            "MIT License",
            "Apache Software License",
        ):
            self.assertIn(license_name, license_classifier)
        # TODO enable assert once a dependency uses 'License-Expression'
        # TODO (maybe black)
        # for license_name in ("MIT",):
        #     self.assertIn(license_name, license_expression)

    def test_find_license_from_classifier(self) -> None:
        classifiers = ["License :: OSI Approved :: MIT License"]
        self.assertEqual(
            ["MIT License"], find_license_from_classifier(classifiers)
        )

    def test_display_multiple_license_from_classifier(self) -> None:
        classifiers = [
            "License :: OSI Approved",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "License :: OSI Approved :: MIT License",
            "License :: Public Domain",
        ]
        self.assertEqual(
            [
                "GNU General Public License v3 (GPLv3)",
                "MIT License",
                "Public Domain",
            ],
            find_license_from_classifier(classifiers),
        )

    def test_if_no_classifiers_then_no_licences_found(self) -> None:
        classifiers: list[str] = []
        self.assertEqual([], find_license_from_classifier(classifiers))

    def test_select_license_by_source(self) -> None:
        self.assertEqual(
            {"MIT License"},
            select_license_by_source(
                FromArg.CLASSIFIER, ["MIT License"], "MIT", LICENSE_UNKNOWN
            ),
        )

        self.assertEqual(
            {LICENSE_UNKNOWN},
            select_license_by_source(
                FromArg.CLASSIFIER, [], "MIT", LICENSE_UNKNOWN
            ),
        )

        self.assertEqual(
            {"MIT License"},
            select_license_by_source(
                FromArg.MIXED, ["MIT License"], "MIT", LICENSE_UNKNOWN
            ),
        )

        self.assertEqual(
            {"MIT"},
            select_license_by_source(
                FromArg.MIXED, [], "MIT", LICENSE_UNKNOWN
            ),
        )
        self.assertEqual(
            {"Apache License 2.0"},
            select_license_by_source(
                FromArg.MIXED,
                ["Apache License 2.0"],
                "Apache-2.0",
                LICENSE_UNKNOWN,
            ),
        )

        self.assertEqual(
            {"MIT"},
            select_license_by_source(
                FromArg.MIXED, [], LICENSE_UNKNOWN, "MIT"
            ),
        )
        self.assertEqual(
            {"Apache-2.0"},
            select_license_by_source(
                FromArg.MIXED,
                ["Apache License 2.0"],
                "Apache",
                "Apache-2.0",
            ),
        )
        self.assertEqual(
            {"Apache-2.0"},
            select_license_by_source(
                FromArg.EXPRESSION,
                ["Apache License 2.0"],
                "Apache",
                "Apache-2.0",
            ),
        )

    def test_with_system(self) -> None:
        with_system_args = ["--with-system"]
        args = self.parser.parse_args(with_system_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        external_sys_pkgs = list(SYSTEM_PACKAGES)
        external_sys_pkgs.remove(__pkgname__)
        for sys_pkg in external_sys_pkgs:
            self.assertIn(sys_pkg, pkg_name_columns)

    def test_with_authors(self) -> None:
        with_authors_args = ["--with-authors"]
        args = self.parser.parse_args(with_authors_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn("Author", output_fields)

        output_string = create_output_string(args)
        self.assertIn("Author", output_string)

    def test_with_maintainers(self) -> None:
        with_maintainers_args = ["--with-maintainers"]
        args = self.parser.parse_args(with_maintainers_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn("Maintainer", output_fields)

        output_string = create_output_string(args)
        self.assertIn("Maintainer", output_string)

    def test_with_urls(self) -> None:
        with_urls_args = ["--with-urls"]
        args = self.parser.parse_args(with_urls_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn("URL", output_fields)

        output_string = create_output_string(args)
        self.assertIn("URL", output_string)

    def test_with_description(self) -> None:
        with_description_args = ["--with-description"]
        args = self.parser.parse_args(with_description_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn("Description", output_fields)

        output_string = create_output_string(args)
        self.assertIn("Description", output_string)

    def test_without_version(self) -> None:
        without_version_args = ["--no-version"]
        args = self.parser.parse_args(without_version_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertNotIn("Version", output_fields)

        output_string = create_output_string(args)
        self.assertNotIn("Version", output_string)

    def test_with_license_file(self) -> None:
        with_license_file_args = ["--with-license-file"]
        args = self.parser.parse_args(with_license_file_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn("LicenseFile", output_fields)
        self.assertIn("LicenseText", output_fields)
        self.assertNotIn("NoticeFile", output_fields)
        self.assertNotIn("NoticeText", output_fields)

        output_string = create_output_string(args)
        self.assertIn("LicenseFile", output_string)
        self.assertIn("LicenseText", output_string)
        self.assertNotIn("NoticeFile", output_string)
        self.assertNotIn("NoticeText", output_string)

    def test_with_notice_file(self) -> None:
        with_license_file_args = ["--with-license-file", "--with-notice-file"]
        args = self.parser.parse_args(with_license_file_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn("LicenseFile", output_fields)
        self.assertIn("LicenseText", output_fields)
        self.assertIn("NoticeFile", output_fields)
        self.assertIn("NoticeText", output_fields)

        output_string = create_output_string(args)
        self.assertIn("LicenseFile", output_string)
        self.assertIn("LicenseText", output_string)
        self.assertIn("NoticeFile", output_string)
        self.assertIn("NoticeText", output_string)

    def test_with_license_file_no_path(self) -> None:
        with_license_file_args = [
            "--with-license-file",
            "--with-notice-file",
            "--no-license-path",
        ]
        args = self.parser.parse_args(with_license_file_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertNotIn("LicenseFile", output_fields)
        self.assertIn("LicenseText", output_fields)
        self.assertNotIn("NoticeFile", output_fields)
        self.assertIn("NoticeText", output_fields)

        output_string = create_output_string(args)
        self.assertNotIn("LicenseFile", output_string)
        self.assertIn("LicenseText", output_string)
        self.assertNotIn("NoticeFile", output_string)
        self.assertIn("NoticeText", output_string)

    def test_with_license_file_warning(self) -> None:
        with_license_file_args = ["--with-license-file", "--format=markdown"]
        args = self.parser.parse_args(with_license_file_args)

        warn_string = create_warn_string(args)
        self.assertIn("best paired with --format=json", warn_string)

    def test_ignore_packages(self) -> None:
        ignore_pkg_name = "prettytable"
        ignore_packages_args = [
            "--ignore-package=" + ignore_pkg_name,
            "--with-system",
        ]
        args = self.parser.parse_args(ignore_packages_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        self.assertNotIn(ignore_pkg_name, pkg_name_columns)

    def test_ignore_normalized_packages(self) -> None:
        ignore_pkg_name = "pip-licenses"
        ignore_packages_args = [
            "--ignore-package=pip_licenses",
            "--with-system",
        ]
        args = self.parser.parse_args(ignore_packages_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        self.assertNotIn(ignore_pkg_name, pkg_name_columns)

    def test_ignore_packages_and_version(self) -> None:
        # Fictitious version that does not exist
        ignore_pkg_name = "prettytable"
        ignore_pkg_spec = ignore_pkg_name + ":1.99.99"
        ignore_packages_args = [
            "--ignore-package=" + ignore_pkg_spec,
            "--with-system",
        ]
        args = self.parser.parse_args(ignore_packages_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        # It is expected that prettytable will include
        self.assertIn(ignore_pkg_name, pkg_name_columns)

    def test_with_packages(self) -> None:
        pkg_name = "pytest"
        only_packages_args = ["--packages=" + pkg_name]
        args = self.parser.parse_args(only_packages_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        self.assertListEqual([pkg_name], pkg_name_columns)

    def test_with_normalized_packages(self) -> None:
        pkg_name = "typing_extensions"
        only_packages_args = [
            "--package=typing-extensions",
            "--with-system",
        ]
        args = self.parser.parse_args(only_packages_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        self.assertListEqual([pkg_name], pkg_name_columns)

    def test_with_packages_with_system(self) -> None:
        pkg_name = "prettytable"
        only_packages_args = ["--packages=" + pkg_name, "--with-system"]
        args = self.parser.parse_args(only_packages_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        self.assertListEqual([pkg_name], pkg_name_columns)

    def test_order_name(self) -> None:
        order_name_args = ["--order=name"]
        args = self.parser.parse_args(order_name_args)

        sortby = get_sortby(args)
        self.assertEqual("Name", sortby)

    def test_order_license(self) -> None:
        order_license_args = ["--order=license"]
        args = self.parser.parse_args(order_license_args)

        sortby = get_sortby(args)
        self.assertEqual("License", sortby)

    def test_order_author(self) -> None:
        order_author_args = ["--order=author", "--with-authors"]
        args = self.parser.parse_args(order_author_args)

        sortby = get_sortby(args)
        self.assertEqual("Author", sortby)

    def test_order_maintainer(self) -> None:
        order_maintainer_args = ["--order=maintainer", "--with-maintainers"]
        args = self.parser.parse_args(order_maintainer_args)

        sortby = get_sortby(args)
        self.assertEqual("Maintainer", sortby)

    def test_order_url(self) -> None:
        order_url_args = ["--order=url", "--with-urls"]
        args = self.parser.parse_args(order_url_args)

        sortby = get_sortby(args)
        self.assertEqual("URL", sortby)

    def test_order_url_no_effect(self) -> None:
        order_url_args = ["--order=url"]
        args = self.parser.parse_args(order_url_args)

        sortby = get_sortby(args)
        self.assertEqual("Name", sortby)

    def test_format_plain(self) -> None:
        format_plain_args = ["--format=plain"]
        args = self.parser.parse_args(format_plain_args)
        table = factory_styled_table_with_args(args)

        self.assertIn("l", table.align.values())
        self.assertFalse(table.border)
        self.assertTrue(table.header)
        self.assertEqual("+", table.junction_char)
        self.assertEqual(HRuleStyle.FRAME, table.hrules)

    def test_format_plain_vertical(self) -> None:
        format_plain_args = ["--format=plain-vertical", "--from=classifier"]
        args = self.parser.parse_args(format_plain_args)
        output_string = create_output_string(args)
        self.assertIsNotNone(
            re.search(r"pytest\n\d\.\d\.\d\nMIT License\n", output_string)
        )

    def test_format_markdown(self) -> None:
        format_markdown_args = ["--format=markdown"]
        args = self.parser.parse_args(format_markdown_args)
        table = create_licenses_table(args)

        self.assertIn("l", table.align.values())
        self.assertTrue(table.border)
        self.assertTrue(table.header)
        self.assertEqual("|", table.junction_char)
        self.assertEqual(HRuleStyle.HEADER, table.hrules)

    @unittest.skipIf(
        sys.version_info < (3, 6, 0),
        "To unsupport Python 3.5 in the near future",
    )
    def test_format_rst_without_filter(self) -> None:
        piplicenses.importlib_metadata.distributions = (
            importlib_metadata_distributions_mocked
        )
        format_rst_args = ["--format=rst"]
        args = self.parser.parse_args(format_rst_args)
        table = create_licenses_table(args)

        self.assertIn("l", table.align.values())
        self.assertTrue(table.border)
        self.assertTrue(table.header)
        self.assertEqual("+", table.junction_char)
        self.assertEqual(HRuleStyle.ALL, table.hrules)
        piplicenses.importlib_metadata.distributions = (
            importlib_metadata_distributions_orig
        )

    def test_format_rst_default_filter(self) -> None:
        piplicenses.importlib_metadata.distributions = (
            importlib_metadata_distributions_mocked
        )
        format_rst_args = ["--format=rst", "--filter-strings"]
        args = self.parser.parse_args(format_rst_args)
        table = create_licenses_table(args)

        self.assertIn("l", table.align.values())
        self.assertTrue(table.border)
        self.assertTrue(table.header)
        self.assertEqual("+", table.junction_char)
        self.assertEqual(HRuleStyle.ALL, table.hrules)
        self.check_rst(str(table))
        piplicenses.importlib_metadata.distributions = (
            importlib_metadata_distributions_orig
        )

    def test_format_confluence(self) -> None:
        format_confluence_args = ["--format=confluence"]
        args = self.parser.parse_args(format_confluence_args)
        table = create_licenses_table(args)

        self.assertIn("l", table.align.values())
        self.assertTrue(table.border)
        self.assertTrue(table.header)
        self.assertEqual("|", table.junction_char)
        self.assertEqual(HRuleStyle.NONE, table.hrules)

    def test_format_html(self) -> None:
        format_html_args = ["--format=html", "--with-authors"]
        args = self.parser.parse_args(format_html_args)
        output_string = create_output_string(args)

        self.assertIn("<table>", output_string)
        self.assertIn("Filipe La&#237;ns", output_string)  # author of "build"

    def test_format_json(self) -> None:
        format_json_args = ["--format=json", "--with-authors"]
        args = self.parser.parse_args(format_json_args)
        output_string = create_output_string(args)

        self.assertIn('"Author":', output_string)
        self.assertNotIn('"URL":', output_string)

    def test_format_json_license_manager(self) -> None:
        format_json_args = ["--format=json-license-finder"]
        args = self.parser.parse_args(format_json_args)
        output_string = create_output_string(args)

        self.assertNotIn('"URL":', output_string)
        self.assertIn('"name":', output_string)
        self.assertIn('"version":', output_string)
        self.assertIn('"licenses":', output_string)

    def test_format_csv(self) -> None:
        format_csv_args = ["--format=csv", "--with-authors"]
        args = self.parser.parse_args(format_csv_args)
        output_string = create_output_string(args)

        obtained_header = output_string.split("\n", 1)[0]
        expected_header = '"Name","Version","License","Author"'
        self.assertEqual(obtained_header, expected_header)

    def test_summary(self) -> None:
        summary_args = ["--summary"]
        args = self.parser.parse_args(summary_args)
        output_string = create_output_string(args)

        self.assertIn("Count", output_string)
        self.assertNotIn("Name", output_string)

        warn_string = create_warn_string(args)
        self.assertTrue(len(warn_string) == 0)

    def test_summary_sort_by_count(self) -> None:
        summary_args = ["--summary", "--order=count"]
        args = self.parser.parse_args(summary_args)

        sortby = get_sortby(args)
        self.assertEqual("Count", sortby)

    def test_summary_sort_by_name(self) -> None:
        summary_args = ["--summary", "--order=name"]
        args = self.parser.parse_args(summary_args)

        sortby = get_sortby(args)
        self.assertEqual("License", sortby)

    def test_summary_warning(self) -> None:
        summary_args = ["--summary", "--with-authors"]
        args = self.parser.parse_args(summary_args)

        warn_string = create_warn_string(args)
        self.assertIn(
            "using --with-authors and --with-urls will be ignored.",
            warn_string,
        )

        summary_args = ["--summary", "--with-urls"]
        args = self.parser.parse_args(summary_args)

        warn_string = create_warn_string(args)
        self.assertIn(
            "using --with-authors and --with-urls will be ignored.",
            warn_string,
        )

    def test_output_colored_normal(self) -> None:
        color_code = "32"
        text = __pkgname__
        actual = output_colored(color_code, text)

        self.assertTrue(actual.startswith("\033[32"))
        self.assertIn(text, actual)
        self.assertTrue(actual.endswith("\033[0m"))

    def test_output_colored_bold(self) -> None:
        color_code = "32"
        text = __pkgname__
        actual = output_colored(color_code, text, is_bold=True)

        self.assertTrue(actual.startswith("\033[1;32"))
        self.assertIn(text, actual)
        self.assertTrue(actual.endswith("\033[0m"))

    def test_without_filter(self) -> None:
        piplicenses.importlib_metadata.distributions = (
            importlib_metadata_distributions_mocked
        )
        args = self.parser.parse_args([])
        packages = list(piplicenses.get_packages(args))
        self.assertIn(UNICODE_APPENDIX, packages[-1]["name"])
        piplicenses.importlib_metadata.distributions = (
            importlib_metadata_distributions_orig
        )

    def test_with_default_filter(self) -> None:
        piplicenses.importlib_metadata.distributions = (
            importlib_metadata_distributions_mocked
        )
        args = self.parser.parse_args(["--filter-strings"])
        packages = list(piplicenses.get_packages(args))
        piplicenses.importlib_metadata.distributions = (
            importlib_metadata_distributions_orig
        )
        self.assertNotIn(UNICODE_APPENDIX, packages[-1]["name"])

    def test_with_specified_filter(self) -> None:
        piplicenses.importlib_metadata.distributions = (
            importlib_metadata_distributions_mocked
        )
        args = self.parser.parse_args(
            ["--filter-strings", "--filter-code-page=ascii"]
        )
        packages = list(piplicenses.get_packages(args))
        self.assertNotIn(UNICODE_APPENDIX, packages[-1]["summary"])
        piplicenses.importlib_metadata.distributions = (
            importlib_metadata_distributions_orig
        )

    def test_case_insensitive_set_diff(self) -> None:
        set_a = {"MIT License"}
        set_b = {"Mit License", "BSD License"}
        set_c = {"mit license"}
        a_diff_b = case_insensitive_set_diff(set_a, set_b)
        a_diff_c = case_insensitive_set_diff(set_a, set_c)
        b_diff_c = case_insensitive_set_diff(set_b, set_c)
        a_diff_empty = case_insensitive_set_diff(set_a, set())

        self.assertTrue(len(a_diff_b) == 0)
        self.assertTrue(len(a_diff_c) == 0)
        self.assertIn("BSD License", b_diff_c)
        self.assertIn("MIT License", a_diff_empty)

    def test_case_insensitive_set_intersect(self) -> None:
        set_a = {"Revised BSD"}
        set_b = {"Apache License", "revised BSD"}
        set_c = {"revised bsd"}
        a_intersect_b = case_insensitive_set_intersect(set_a, set_b)
        a_intersect_c = case_insensitive_set_intersect(set_a, set_c)
        b_intersect_c = case_insensitive_set_intersect(set_b, set_c)
        a_intersect_empty = case_insensitive_set_intersect(set_a, set())

        self.assertTrue(set_a == a_intersect_b)
        self.assertTrue(set_a == a_intersect_c)
        self.assertTrue({"revised BSD"} == b_intersect_c)
        self.assertTrue(len(a_intersect_empty) == 0)

    def test_case_insensitive_partial_match_set_diff(self) -> None:
        set_a = {"MIT License"}
        set_b = {"Mit", "BSD License"}
        set_c = {"mit license"}
        a_diff_b = case_insensitive_partial_match_set_diff(set_a, set_b)
        a_diff_c = case_insensitive_partial_match_set_diff(set_a, set_c)
        b_diff_c = case_insensitive_partial_match_set_diff(set_b, set_c)
        a_diff_empty = case_insensitive_partial_match_set_diff(set_a, set())

        self.assertTrue(len(a_diff_b) == 0)
        self.assertTrue(len(a_diff_c) == 0)
        self.assertIn("BSD License", b_diff_c)
        self.assertIn("MIT License", a_diff_empty)

    def test_case_insensitive_partial_match_set_intersect(self) -> None:
        set_a = {"Revised BSD"}
        set_b = {"Apache License", "revised BSD"}
        set_c = {"bsd"}
        a_intersect_b = case_insensitive_partial_match_set_intersect(
            set_a, set_b
        )
        a_intersect_c = case_insensitive_partial_match_set_intersect(
            set_a, set_c
        )
        b_intersect_c = case_insensitive_partial_match_set_intersect(
            set_b, set_c
        )
        a_intersect_empty = case_insensitive_partial_match_set_intersect(
            set_a, set()
        )

        self.assertTrue(set_a == a_intersect_b)
        self.assertTrue(set_a == a_intersect_c)
        self.assertTrue({"revised BSD"} == b_intersect_c)
        self.assertTrue(len(a_intersect_empty) == 0)


class MockStdStream(object):
    def __init__(self) -> None:
        self.printed = ""

    def write(self, p) -> None:
        self.printed = p


def test_output_file_success(monkeypatch) -> None:
    def mocked_open(*args, **kwargs):
        import tempfile

        return tempfile.TemporaryFile("w")

    mocked_stdout = MockStdStream()
    mocked_stderr = MockStdStream()
    monkeypatch.setattr(piplicenses, "open", mocked_open)
    monkeypatch.setattr(sys.stdout, "write", mocked_stdout.write)
    monkeypatch.setattr(sys.stderr, "write", mocked_stderr.write)
    monkeypatch.setattr(sys, "exit", lambda n: None)

    save_if_needs("/foo/bar.txt", "license list")
    assert "created path: " in mocked_stdout.printed
    assert "" == mocked_stderr.printed


def test_output_file_error(monkeypatch) -> None:
    def mocked_open(*args, **kwargs):
        raise IOError

    mocked_stdout = MockStdStream()
    mocked_stderr = MockStdStream()
    monkeypatch.setattr(piplicenses, "open", mocked_open)
    monkeypatch.setattr(sys.stdout, "write", mocked_stdout.write)
    monkeypatch.setattr(sys.stderr, "write", mocked_stderr.write)
    monkeypatch.setattr(sys, "exit", lambda n: None)

    save_if_needs("/foo/bar.txt", "license list")
    assert "" == mocked_stdout.printed
    assert "check path: " in mocked_stderr.printed


def test_output_file_none(monkeypatch) -> None:
    mocked_stdout = MockStdStream()
    mocked_stderr = MockStdStream()
    monkeypatch.setattr(sys.stdout, "write", mocked_stdout.write)
    monkeypatch.setattr(sys.stderr, "write", mocked_stderr.write)

    save_if_needs(None, "license list")
    # stdout and stderr are expected not to be called
    assert "" == mocked_stdout.printed
    assert "" == mocked_stderr.printed


def test_allow_only(monkeypatch) -> None:
    licenses = (
        "Bsd License",
        "Apache Software License",
        "Mozilla Public License 2.0 (MPL 2.0)",
        "Python Software Foundation License",
        "Public Domain",
        "GNU General Public License (GPL)",
        "GNU Library or Lesser General Public License (LGPL)",
    )
    allow_only_args = ["--allow-only={}".format(";".join(licenses))]
    mocked_stdout = MockStdStream()
    mocked_stderr = MockStdStream()
    monkeypatch.setattr(sys.stdout, "write", mocked_stdout.write)
    monkeypatch.setattr(sys.stderr, "write", mocked_stderr.write)
    monkeypatch.setattr(sys, "exit", lambda n: None)
    args = create_parser().parse_args(allow_only_args)
    create_licenses_table(args)

    assert "" == mocked_stdout.printed
    assert (
        "license MIT License not in allow-only licenses was found for "
        "package" in mocked_stderr.printed
    )


def test_allow_only_partial(monkeypatch) -> None:
    licenses = (
        "Bsd",
        "Apache",
        "Mozilla Public License 2.0 (MPL 2.0)",
        "Python Software Foundation License",
        "Public Domain",
        "GNU General Public License (GPL)",
        "GNU Library or Lesser General Public License (LGPL)",
    )
    allow_only_args = [
        "--partial-match",
        "--allow-only={}".format(";".join(licenses)),
    ]
    mocked_stdout = MockStdStream()
    mocked_stderr = MockStdStream()
    monkeypatch.setattr(sys.stdout, "write", mocked_stdout.write)
    monkeypatch.setattr(sys.stderr, "write", mocked_stderr.write)
    monkeypatch.setattr(sys, "exit", lambda n: None)
    args = create_parser().parse_args(allow_only_args)
    create_licenses_table(args)

    assert "" == mocked_stdout.printed
    assert (
        "license MIT License not in allow-only licenses was found for "
        "package" in mocked_stderr.printed
    )


def test_different_python() -> None:
    import tempfile

    class TempEnvBuild(venv.EnvBuilder):
        def post_setup(self, context: SimpleNamespace) -> None:
            self.context = context

    with tempfile.TemporaryDirectory() as target_dir_path:
        venv_builder = TempEnvBuild(with_pip=True)
        venv_builder.create(str(target_dir_path))
        python_exec = venv_builder.context.env_exe
        python_arg = f"--python={python_exec}"
        args = create_parser().parse_args([python_arg, "-s", "-f=json"])
        pkgs = get_packages(args)
        package_names = sorted(set(p["name"] for p in pkgs))
        print(package_names)

    expected_packages = ["pip"]
    if sys.version_info < (3, 12, 0):
        expected_packages.append("setuptools")
    assert package_names == expected_packages


def test_fail_on(monkeypatch) -> None:
    licenses = ("MIT license",)
    allow_only_args = ["--fail-on={}".format(";".join(licenses))]
    mocked_stdout = MockStdStream()
    mocked_stderr = MockStdStream()
    monkeypatch.setattr(sys.stdout, "write", mocked_stdout.write)
    monkeypatch.setattr(sys.stderr, "write", mocked_stderr.write)
    monkeypatch.setattr(sys, "exit", lambda n: None)
    args = create_parser().parse_args(allow_only_args)
    create_licenses_table(args)

    assert "" == mocked_stdout.printed
    assert (
        "fail-on license MIT License was found for "
        "package" in mocked_stderr.printed
    )


def test_fail_on_partial_match(monkeypatch) -> None:
    licenses = ("MIT",)
    allow_only_args = [
        "--partial-match",
        "--fail-on={}".format(";".join(licenses)),
    ]
    mocked_stdout = MockStdStream()
    mocked_stderr = MockStdStream()
    monkeypatch.setattr(sys.stdout, "write", mocked_stdout.write)
    monkeypatch.setattr(sys.stderr, "write", mocked_stderr.write)
    monkeypatch.setattr(sys, "exit", lambda n: None)
    args = create_parser().parse_args(allow_only_args)
    create_licenses_table(args)

    assert "" == mocked_stdout.printed
    assert (
        "fail-on license MIT License was found for "
        "package" in mocked_stderr.printed
    )


def test_enums() -> None:
    class TestEnum(Enum):
        PLAIN = P = auto()
        JSON_LICENSE_FINDER = JLF = auto()

    assert TestEnum.PLAIN == TestEnum.P
    assert (
        getattr(TestEnum, value_to_enum_key("jlf"))
        == TestEnum.JSON_LICENSE_FINDER
    )
    assert value_to_enum_key("jlf") == "JLF"
    assert value_to_enum_key("json-license-finder") == "JSON_LICENSE_FINDER"
    assert (
        enum_key_to_value(TestEnum.JSON_LICENSE_FINDER)
        == "json-license-finder"
    )
    assert enum_key_to_value(TestEnum.PLAIN) == "plain"


@pytest.fixture(scope="package")
def parser() -> CompatibleArgumentParser:
    return create_parser()


def test_verify_args(
    parser: CompatibleArgumentParser, capsys: CaptureFixture
) -> None:
    # --with-license-file missing
    with pytest.raises(SystemExit) as ex:
        parser.parse_args(["--no-license-path"])
    capture = capsys.readouterr().err
    for arg in ("--no-license-path", "--with-license-file"):
        assert arg in capture

    with pytest.raises(SystemExit) as ex:
        parser.parse_args(["--with-notice-file"])
    capture = capsys.readouterr().err
    for arg in ("--with-notice-file", "--with-license-file"):
        assert arg in capture

    # --filter-strings missing
    with pytest.raises(SystemExit) as ex:
        parser.parse_args(["--filter-code-page=utf8"])
    capture = capsys.readouterr().err
    for arg in ("--filter-code-page", "--filter-strings"):
        assert arg in capture

    # invalid code-page
    with pytest.raises(SystemExit) as ex:
        parser.parse_args(["--filter-strings", "--filter-code-page=XX"])
    capture = capsys.readouterr().err
    for arg in ("invalid code", "--filter-code-page"):
        assert arg in capture


def test_normalize_pkg_name() -> None:
    expected_normalized_name = "pip-licenses"

    assert normalize_pkg_name("pip_licenses") == expected_normalized_name
    assert normalize_pkg_name("pip.licenses") == expected_normalized_name
    assert normalize_pkg_name("Pip-Licenses") == expected_normalized_name


def test_normalize_version():
    """
    Test normalize_version function with various version strings.
    """
    # Test 1: Simple release version
    assert normalize_version("1.0.0") == "1.0.0"
    # Test 2: Version with 'v' prefix
    assert normalize_version("v2.0.0") == "2.0.0"
    # Test 3: Pre-release version
    assert normalize_version("1.0.0-alpha") == "1.0.0alpha"
    # Test 4: Beta pre-release version
    assert normalize_version("1.0.0-beta.1") == "1.0.0beta1"
    # Test 5: Release candidate version
    assert normalize_version("2.0.0-rc.1") == "2.0.0rc1"
    # Test 6: Post-release version
    assert normalize_version("1.0.0.post1") == "1.0.0post1"
    # Test 7: Development release version
    assert normalize_version("1.0.0.dev3") == "1.0.0dev3"
    # Test 8: Local version
    assert normalize_version("1.2.3+local") == "1.2.3+local"
    # Test 9: Pre-release with local version
    assert normalize_version("1.0.0-alpha.1+local") == "1.0.0alpha1+local"
    # Test 10: Complex version with all match groups
    assert (
        normalize_version("2.0.0-beta.3.post2.dev1") == "2.0.0beta3post2dev1"
    )


def test_normalize_pkg_name_and_version() -> None:
    assert (
        normalize_pkg_name_and_version("pip_licenses:5.5.0")
        == "pip-licenses:5.5.0"
    )
    # Test case 0: Standard package name without version
    assert normalize_pkg_name_and_version("pip_licenses") == "pip-licenses"

    # Test case 1: Standard package name with version
    assert (
        normalize_pkg_name_and_version("requests:2.25.1")
        == normalize_pkg_name("requests") + ":2.25.1"
    )

    # Test case 2: Package name without version
    assert (
        normalize_pkg_name_and_version("flask")
        == normalize_pkg_name("flask") + ""
    )

    # Test case 3: Package name with leading/trailing spaces
    assert (
        normalize_pkg_name_and_version("  numpy : 1.19.5  ")
        == normalize_pkg_name("numpy") + ":1.19.5"
    )

    # Test case 4: Package name with special characters
    assert (
        normalize_pkg_name_and_version("Pillow:8.0.1")
        == normalize_pkg_name("Pillow") + ":8.0.1"
    )

    # Test case 5: Package name with no version and special characters
    assert (
        normalize_pkg_name_and_version("  SciPy  ")
        == normalize_pkg_name("SciPy") + ""
    )

    # Test case 6: Package name with multiple colons
    # (e.g., only the first : should be considered)
    assert (
        normalize_pkg_name_and_version("matplotlib:3.3.0:extra")
        == normalize_pkg_name("matplotlib") + ":"
    )

    # Test case 7: Package name with version in a different format
    assert (
        normalize_pkg_name_and_version("setuptools:56.0.0")
        == normalize_pkg_name("setuptools") + ":56.0.0"
    )

    # Test case 8: Empty input
    assert normalize_pkg_name_and_version("") == ""


def test_extract_homepage_home_page_set() -> None:
    metadata = MagicMock()
    metadata.get.return_value = "Foobar"

    assert "Foobar" == extract_homepage(metadata=metadata)  # type: ignore

    metadata.get.assert_called_once_with("home-page", None)


def test_extract_homepage_project_url_fallback() -> None:
    metadata = MagicMock()
    metadata.get.return_value = None

    # `Homepage` is prioritized higher than `Source`
    metadata.get_all.return_value = [
        "Source, source",
        "Homepage, homepage",
    ]

    assert "homepage" == extract_homepage(metadata=metadata)  # type: ignore

    metadata.get_all.assert_called_once_with("Project-URL", [])


def test_extract_homepage_project_url_fallback_multiple_parts() -> None:
    metadata = MagicMock()
    metadata.get.return_value = None

    # `Homepage` is prioritized higher than `Source`
    metadata.get_all.return_value = [
        "Source, source",
        "Homepage, homepage, foo, bar",
    ]

    assert "homepage, foo, bar" == extract_homepage(
        metadata=metadata  # type: ignore
    )

    metadata.get_all.assert_called_once_with("Project-URL", [])


def test_extract_homepage_empty() -> None:
    metadata = MagicMock()

    metadata.get.return_value = None
    metadata.get_all.return_value = []

    assert None is extract_homepage(metadata=metadata)  # type: ignore

    metadata.get.assert_called_once_with("home-page", None)
    metadata.get_all.assert_called_once_with("Project-URL", [])


def test_extract_homepage_project_uprl_fallback_capitalisation() -> None:
    metadata = MagicMock()
    metadata.get.return_value = None

    # `homepage` is still prioritized higher than `Source` (capitalisation)
    metadata.get_all.return_value = [
        "Source, source",
        "homepage, homepage",
    ]

    assert "homepage" == extract_homepage(metadata=metadata)  # type: ignore

    metadata.get_all.assert_called_once_with("Project-URL", [])


def test_pyproject_toml_args_parsed_correctly():
    # we test that parameters of different types are deserialized correctly
    pyptoject_conf = {
        "tool": {
            __pkgname__: {
                # choices_from_enum
                "from": "classifier",
                # bool
                "summary": True,
                # list[str]
                "ignore-packages": ["package1", "package2"],
                # str
                "fail-on": "LIC1;LIC2",
            }
        }
    }

    toml_str = tomli_w.dumps(pyptoject_conf)

    # Create a temporary file and write the TOML string to it
    with tempfile.NamedTemporaryFile(
        suffix=".toml", delete=False
    ) as temp_file:
        temp_file.write(toml_str.encode("utf-8"))

    parser = create_parser(temp_file.name)
    args = parser.parse_args([])

    tool_conf = pyptoject_conf["tool"][__pkgname__]

    # assert values are correctly parsed from toml
    assert args.from_ == FromArg.CLASSIFIER
    assert args.summary == tool_conf["summary"]
    assert args.ignore_packages == tool_conf["ignore-packages"]
    assert args.fail_on == tool_conf["fail-on"]

    # assert args are rewritable using cli
    args = parser.parse_args(["--from=meta"])

    assert args.from_ != FromArg.CLASSIFIER
    assert args.from_ == FromArg.META

    # all other are parsed from toml
    assert args.summary == tool_conf["summary"]
    assert args.ignore_packages == tool_conf["ignore-packages"]
    assert args.fail_on == tool_conf["fail-on"]

    os.unlink(temp_file.name)


def test_case_insensitive_partial_match_set_diff():
    set_a = {"Python", "Java", "C++"}
    set_b = {"Ruby", "JavaScript"}
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert (
        result == set_a
    ), "When no overlap, the result should be the same as set_a."

    set_a = {"Hello", "World"}
    set_b = {"hello", "world"}
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert (
        result == set()
    ), "When all items overlap, the result should be an empty set."

    set_a = {"HelloWorld", "Python", "JavaScript"}
    set_b = {"hello", "script"}
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert result == {
        "Python"
    }, "Only 'Python' should remain as it has no overlap with set_b."

    set_a = {"HELLO", "world"}
    set_b = {"hello"}
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert result == {
        "world"
    }, "The function should handle case-insensitive matches correctly."

    set_a = set()
    set_b = set()
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert (
        result == set()
    ), "When both sets are empty, the result should also be empty."

    set_a = {"Python", "Java"}
    set_b = set()
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert (
        result == set_a
    ), "If set_b is empty, result should be the same as set_a."

    set_a = set()
    set_b = {"Ruby"}
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert (
        result == set()
    ), "If set_a is empty, result should be empty regardless of set_b."

    set_a = {"BSD License", "MIT License"}
    set_b = {"BSD"}
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert result == {
        "MIT License"
    }, "The function should match partials (exclusively)."

    set_a = {"BSD", "BSD License"}
    set_b = {"BSD"}
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert result == set(), "The function should match partials (inclusively)."

    set_a = {"Apache-2.0 OR BSD-3-Clause"}
    set_b = {"BSD", "Apache"}
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert result == set(), "Multiple matches shouldn't crash."

    set_a = {"Duplicate", "duplicate", "Unique"}
    set_b = {"unique"}
    result = sorted(case_insensitive_partial_match_set_diff(set_a, set_b))
    expected_order = sorted({"Duplicate", "duplicate"})
    assert (
        result == expected_order
    ), "The function should still preserve case of set_a (order-insensitive)."

    set_a = {"Test", "Example"}
    set_b = {"Sample", "Test"}
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert result == {
        "Example"
    }, "If only part of set_b matches set_a non-matches should have no impact."

    set_a = {"A", "B", "C"}
    set_b = {"D", "E"}
    result = sorted(case_insensitive_partial_match_set_diff(set_a, set_b))
    expected_order = sorted({"A", "B", "C"})
    assert (
        result == expected_order
    ), "Non-overlapping sets should preserve all of set_a (order-insensitive)."
