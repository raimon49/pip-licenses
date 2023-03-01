# -*- coding: utf-8 -*-
# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et
from __future__ import annotations

import copy
import email
import re
import sys
import unittest
from enum import Enum, auto
from importlib.metadata import Distribution
from typing import TYPE_CHECKING, Any, List

import docutils.frontend
import docutils.parsers.rst
import docutils.utils
import pytest
from _pytest.capture import CaptureFixture

import piplicenses
from piplicenses import (
    DEFAULT_OUTPUT_FIELDS,
    LICENSE_UNKNOWN,
    RULE_ALL,
    RULE_FRAME,
    RULE_HEADER,
    RULE_NONE,
    SYSTEM_PACKAGES,
    CompatibleArgumentParser,
    FromArg,
    __pkgname__,
    case_insensitive_set_diff,
    case_insensitive_set_intersect,
    create_licenses_table,
    create_output_string,
    create_parser,
    create_warn_string,
    enum_key_to_value,
    factory_styled_table_with_args,
    find_license_from_classifier,
    get_output_fields,
    get_sortby,
    output_colored,
    save_if_needs,
    select_license_by_source,
    value_to_enum_key,
)

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
        self.assertEqual(RULE_FRAME, table.hrules)

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

    def test_from_all(self) -> None:
        from_args = ["--from=all"]
        args = self.parser.parse_args(from_args)
        output_fields = get_output_fields(args)
        table = create_licenses_table(args, output_fields)

        self.assertIn("License-Metadata", output_fields)
        self.assertIn("License-Classifier", output_fields)

        index_license_meta = output_fields.index("License-Metadata")
        license_meta = []
        for row in table.rows:
            license_meta.append(row[index_license_meta])

        index_license_classifier = output_fields.index("License-Classifier")
        license_classifier = []
        for row in table.rows:
            license_classifier.append(row[index_license_classifier])

        for license_name in ("BSD", "MIT", "Apache 2.0"):
            self.assertIn(license_name, license_meta)
        for license_name in (
            "BSD License",
            "MIT License",
            "Apache Software License",
        ):
            self.assertIn(license_name, license_classifier)

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
        classifiers: List[str] = []
        self.assertEqual([], find_license_from_classifier(classifiers))

    def test_select_license_by_source(self) -> None:
        self.assertEqual(
            {"MIT License"},
            select_license_by_source(
                FromArg.CLASSIFIER, ["MIT License"], "MIT"
            ),
        )

        self.assertEqual(
            {LICENSE_UNKNOWN},
            select_license_by_source(FromArg.CLASSIFIER, [], "MIT"),
        )

        self.assertEqual(
            {"MIT License"},
            select_license_by_source(FromArg.MIXED, ["MIT License"], "MIT"),
        )

        self.assertEqual(
            {"MIT"}, select_license_by_source(FromArg.MIXED, [], "MIT")
        )
        self.assertEqual(
            {"Apache License 2.0"},
            select_license_by_source(
                FromArg.MIXED, ["Apache License 2.0"], "Apache-2.0"
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
        if "PTable" in SYSTEM_PACKAGES:
            ignore_pkg_name = "PTable"
        else:
            ignore_pkg_name = "prettytable"
        ignore_packages_args = ["--ignore-package=" + ignore_pkg_name]
        args = self.parser.parse_args(ignore_packages_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        self.assertNotIn(ignore_pkg_name, pkg_name_columns)

    def test_with_packages(self) -> None:
        pkg_name = "py"
        only_packages_args = ["--packages=" + pkg_name]
        args = self.parser.parse_args(only_packages_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        self.assertListEqual([pkg_name], pkg_name_columns)

    def test_with_packages_with_system(self) -> None:
        if "PTable" in SYSTEM_PACKAGES:
            pkg_name = "PTable"
        else:
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
        self.assertEqual(RULE_FRAME, table.hrules)

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
        self.assertEqual(RULE_HEADER, table.hrules)

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
        self.assertEqual(RULE_ALL, table.hrules)
        with self.assertRaises(docutils.utils.SystemMessage):
            self.check_rst(str(table))
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
        self.assertEqual(RULE_ALL, table.hrules)
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
        self.assertEqual(RULE_NONE, table.hrules)

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
