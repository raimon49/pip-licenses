# reduce to relevant parts to ensure Stefan is credited
# for content from https://github.com/stefan6419846/pip-licenses-cli/commit/0b1c2ae56d0d8bd0bac078bf758cc770da5527b0
# From Stefan's Pip-liceses-cli:
# Copyright (c) 2025 stefan6419846
# with MIT License (See LICENSE.txt; but this file had no included content, assumed not substantial portion?)

# But let's reduce further to what is of interest
# a big thank you to Stefan AKA stefan6419846 for their work on this!

from piplicenses.cli import (
    create_output_string,
    create_parser,
    create_warn_string,
    enum_key_to_value,
    get_output_fields,
    get_sortby,
    load_config_from_file,
    output_colored,
    save_if_needs,
    value_to_enum_key,
)


class CreateWarnStringTestCase(CommandLineTestCase):
    """From Code Copyrighted by Stefan
       Copyright (c) 2025 stefan6419846"""
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

    def test_with_license_files_format_warning(self) -> None:
        args = self.parser.parse_args(["--format=html", "--with-license-files"])
        warn_string = create_warn_string(args)
        self.assertIn("Ignoring request to output multiple files due to unsupported output format.", warn_string)

        args = self.parser.parse_args(["--format=json", "--with-license-files"])
        warn_string = create_warn_string(args)
        self.assertNotIn("Ignoring request to output multiple files due to unsupported output format.", warn_string)


class GetSortbyTestCase(CommandLineTestCase):
    def test_summary_sort_by_count(self) -> None:
        pass

    def reduced_to_ref_point_for_diff():

        sortby = get_sortby(args)
        self.assertEqual("Name", sortby)


class GetOutputFieldsTestCase(CommandLineTestCase):
    """From Code Copyrighted by Stefan
       Copyright (c) 2025 stefan6419846"""
    def test_with_license_files(self) -> None:
        for format_string in ["json", "plain-vertical"]:
            with self.subTest(format_string=format_string):
                args = self.parser.parse_args(["--with-license-files", f"--format={format_string}", "--with-notice-files", "--with-other-files"])
                fields = get_output_fields(args)
                self.assertEqual(
                    ["Name", "Version", "License", "LicenseFiles", "LicenseTexts", "NoticeFiles", "NoticeTexts", "OtherFiles", "OtherTexts"], fields
                )

        for format_string in ["plain", "csv", "html"]:
            with self.subTest(format_string=format_string):
                args = self.parser.parse_args(["--with-license-files", f"--format={format_string}", "--with-notice-files", "--with-other-files"])
                fields = get_output_fields(args)
                self.assertEqual(["Name", "Version", "License"], fields)

    def test_files_singular_plural(self) -> None:
        args = self.parser.parse_args(
            [
                "--with-license-file",
                "--format=json",
                "--with-notice-file",
                "--with-other-files",
            ]
        )
        fields = get_output_fields(args)
        self.assertEqual(["Name", "Version", "License", "LicenseFile", "LicenseText", "NoticeFile", "NoticeText", "OtherFiles", "OtherTexts"], fields)

        args = self.parser.parse_args(
            [
                "--with-license-files",
                "--format=json",
                "--with-notice-files",
                "--with-other-files",
            ]
        )
        fields = get_output_fields(args)
        self.assertEqual(["Name", "Version", "License", "LicenseFiles", "LicenseTexts", "NoticeFiles", "NoticeTexts", "OtherFiles", "OtherTexts"], fields)

    def test_no_license_path(self) -> None:
        args = self.parser.parse_args(
            [
                "--with-license-files",
                "--format=json",
                "--with-notice-files",
                "--with-other-files",
            ]
        )
        fields = get_output_fields(args)
        self.assertEqual(["Name", "Version", "License", "LicenseFiles", "LicenseTexts", "NoticeFiles", "NoticeTexts", "OtherFiles", "OtherTexts"], fields)

        args = self.parser.parse_args(
            [
                "--with-license-files",
                "--format=json",
                "--with-notice-files",
                "--with-other-files",
                "--no-license-path",
            ]
        )
        fields = get_output_fields(args)
        self.assertEqual(["Name", "Version", "License", "LicenseTexts", "NoticeTexts", "OtherTexts"], fields)
