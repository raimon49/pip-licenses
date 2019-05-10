from __future__ import (division, print_function,
                        absolute_import, unicode_literals)
import unittest
from email import message_from_string

from prettytable.prettytable import (FRAME as RULE_FRAME, ALL as RULE_ALL,
                                     HEADER as RULE_HEADER, NONE as RULE_NONE)
from piplicenses import (__pkgname__, create_parser, output_colored,
                         create_licenses_table, get_output_fields, get_sortby,
                         factory_styled_table_with_args, create_warn_string,
                         find_license_from_classifier, create_output_string,
                         DEFAULT_OUTPUT_FIELDS, SYSTEM_PACKAGES,
                         LICENSE_UNKNOWN)


class CommandLineTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = create_parser()


class TestGetLicenses(CommandLineTestCase):
    def setUp(self):
        pass

    def _create_pkg_name_columns(self, table):
        import copy
        index = DEFAULT_OUTPUT_FIELDS.index('Name')

        # XXX: access to private API
        rows = copy.deepcopy(table._rows)
        pkg_name_columns = []
        for row in rows:
            pkg_name_columns.append(row[index])

        return pkg_name_columns

    def _create_license_columns(self, table):
        import copy
        index = DEFAULT_OUTPUT_FIELDS.index('License')

        # XXX: access to private API
        rows = copy.deepcopy(table._rows)
        pkg_name_columns = []
        for row in rows:
            pkg_name_columns.append(row[index])

        return pkg_name_columns

    def test_with_empty_args(self):
        empty_args = []
        args = self.parser.parse_args(empty_args)
        table = create_licenses_table(args)

        self.assertIn('l', table.align.values())
        self.assertFalse(table.border)
        self.assertTrue(table.header)
        self.assertEqual('+', table.junction_char)
        self.assertEqual(RULE_FRAME, table.hrules)

        output_fields = get_output_fields(args)
        self.assertEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertNotIn('Author', output_fields)
        self.assertNotIn('URL', output_fields)

        pkg_name_columns = self._create_pkg_name_columns(table)
        for sys_pkg in SYSTEM_PACKAGES:
            self.assertNotIn(sys_pkg, pkg_name_columns)

        sortby = get_sortby(args)
        self.assertEqual('Name', sortby)

        output_string = create_output_string(args)
        self.assertNotIn('<table>', output_string)

    def test_from_classifier(self):
        from_classifier_args = ['--from=classifier']
        args = self.parser.parse_args(from_classifier_args)
        table = create_licenses_table(args)

        output_fields = get_output_fields(args)
        self.assertIn('License', output_fields)

        license_columns = self._create_license_columns(table)
        license_notation_as_classifier = 'MIT License'
        self.assertIn(license_notation_as_classifier, license_columns)

    def test_find_license_from_classifier(self):
        metadata = ('Metadata-Version: 2.0\r\n'
                    'Name: pip-licenses\r\n'
                    'Version: 1.0.0\r\n'
                    'Classifier: License :: OSI Approved :: MIT License\r\n')
        message = message_from_string(metadata)
        self.assertEqual('MIT License',
                         find_license_from_classifier(message))

    def test_display_multiple_license_from_classifier(self):
        metadata = ('Metadata-Version: 2.0\r\n'
                    'Name: helga\r\n'
                    'Version: 1.7.6\r\n'
                    'Classifier: License :: OSI Approved\r\n'
                    'Classifier: License :: OSI Approved :: '
                    'GNU General Public License v3 (GPLv3)\r\n'
                    'Classifier: License :: OSI Approved :: MIT License\r\n'
                    'Classifier: License :: Public Domain\r\n')
        message = message_from_string(metadata)
        self.assertEqual('GNU General Public License v3 (GPLv3), '
                         'MIT License, '
                         'Public Domain',
                         find_license_from_classifier(message))

    def test_not_found_license_from_classifier(self):
        metadata_as_no_license = ('Metadata-Version: 2.0\r\n'
                                  'Name: pip-licenses\r\n'
                                  'Version: 1.0.0\r\n')
        message = message_from_string(metadata_as_no_license)
        self.assertEqual(LICENSE_UNKNOWN,
                         find_license_from_classifier(message))

    def test_with_system(self):
        with_system_args = ['--with-system']
        args = self.parser.parse_args(with_system_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        external_sys_pkgs = list(SYSTEM_PACKAGES)
        external_sys_pkgs.remove(__pkgname__)
        for sys_pkg in external_sys_pkgs:
            self.assertIn(sys_pkg, pkg_name_columns)

    def test_with_authors(self):
        with_authors_args = ['--with-authors']
        args = self.parser.parse_args(with_authors_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn('Author', output_fields)

        output_string = create_output_string(args)
        self.assertIn('Author', output_string)

    def test_with_urls(self):
        with_urls_args = ['--with-urls']
        args = self.parser.parse_args(with_urls_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn('URL', output_fields)

        output_string = create_output_string(args)
        self.assertIn('URL', output_string)

    def test_with_description(self):
        with_description_args = ['--with-description']
        args = self.parser.parse_args(with_description_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn('Description', output_fields)

        output_string = create_output_string(args)
        self.assertIn('Description', output_string)

    def test_with_license_file(self):
        with_license_file_args = ['--with-license-file']
        args = self.parser.parse_args(with_license_file_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn('LicenseFile', output_fields)
        self.assertIn('LicenseText', output_fields)

        output_string = create_output_string(args)
        self.assertIn('LicenseFile', output_string)
        self.assertIn('LicenseText', output_string)

    def test_with_license_file_warning(self):
        with_license_file_args = ['--with-license-file', '--format=markdown']
        args = self.parser.parse_args(with_license_file_args)

        warn_string = create_warn_string(args)
        self.assertIn('best paired with --format=json', warn_string)

    def test_ignore_packages(self):
        ignore_pkg_name = 'PTable'
        ignore_packages_args = ['--ignore-package=' + ignore_pkg_name]
        args = self.parser.parse_args(ignore_packages_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        self.assertNotIn(ignore_pkg_name, pkg_name_columns)

    def test_order_name(self):
        order_name_args = ['--order=name']
        args = self.parser.parse_args(order_name_args)

        sortby = get_sortby(args)
        self.assertEqual('Name', sortby)

    def test_order_license(self):
        order_license_args = ['--order=license']
        args = self.parser.parse_args(order_license_args)

        sortby = get_sortby(args)
        self.assertEqual('License', sortby)

    def test_order_author(self):
        order_author_args = ['--order=author', '--with-authors']
        args = self.parser.parse_args(order_author_args)

        sortby = get_sortby(args)
        self.assertEqual('Author', sortby)

    def test_order_url(self):
        order_url_args = ['--order=url', '--with-urls']
        args = self.parser.parse_args(order_url_args)

        sortby = get_sortby(args)
        self.assertEqual('URL', sortby)

    def test_order_url_no_effect(self):
        order_url_args = ['--order=url']
        args = self.parser.parse_args(order_url_args)

        sortby = get_sortby(args)
        self.assertEqual('Name', sortby)

    def test_format_plain(self):
        format_plain_args = ['--format=plain']
        args = self.parser.parse_args(format_plain_args)
        table = factory_styled_table_with_args(args)

        self.assertIn('l', table.align.values())
        self.assertFalse(table.border)
        self.assertTrue(table.header)
        self.assertEqual('+', table.junction_char)
        self.assertEqual(RULE_FRAME, table.hrules)

    def test_format_markdown(self):
        format_markdown_args = ['--format=markdown']
        args = self.parser.parse_args(format_markdown_args)
        table = factory_styled_table_with_args(args)

        self.assertIn('l', table.align.values())
        self.assertTrue(table.border)
        self.assertTrue(table.header)
        self.assertEqual('|', table.junction_char)
        self.assertEqual(RULE_HEADER, table.hrules)

    def test_format_rst(self):
        format_rst_args = ['--format=rst']
        args = self.parser.parse_args(format_rst_args)
        table = factory_styled_table_with_args(args)

        self.assertIn('l', table.align.values())
        self.assertTrue(table.border)
        self.assertTrue(table.header)
        self.assertEqual('+', table.junction_char)
        self.assertEqual(RULE_ALL, table.hrules)

    def test_format_confluence(self):
        format_confluence_args = ['--format=confluence']
        args = self.parser.parse_args(format_confluence_args)
        table = factory_styled_table_with_args(args)

        self.assertIn('l', table.align.values())
        self.assertTrue(table.border)
        self.assertTrue(table.header)
        self.assertEqual('|', table.junction_char)
        self.assertEqual(RULE_NONE, table.hrules)

    def test_format_html(self):
        format_html_args = ['--format=html']
        args = self.parser.parse_args(format_html_args)
        output_string = create_output_string(args)

        self.assertIn('<table>', output_string)

    def test_format_json(self):
        format_json_args = ['--format=json', '--with-authors']
        args = self.parser.parse_args(format_json_args)
        output_string = create_output_string(args)

        self.assertIn('"Author":', output_string)
        self.assertNotIn('"URL":', output_string)

    def test_format_csv(self):
        format_csv_args = ['--format-csv', '--with-authors']
        args = self.parser.parse_args(format_csv_args)
        output_string = create_output_string(args)

        obtained_header = output_string.split('\n', 1)[0]
        expected_header = '"Version","Name","License","Author"'
        self.assertEqual(obtained_header, expected_header)

    def test_from_compatibility(self):
        from_old_style_args = ['--from-classifier']
        args = self.parser.parse_args(from_old_style_args)
        warn_string = create_warn_string(args)

        self.assertEqual('classifier', getattr(args, 'from'))
        self.assertIn('deprecated', warn_string)

    def test_format_compatibility(self):
        format_old_style_args = ['--format-markdown']
        args = self.parser.parse_args(format_old_style_args)
        warn_string = create_warn_string(args)

        self.assertEqual('markdown', args.format)
        self.assertIn('deprecated', warn_string)

        format_old_style_args = ['--format-rst']
        args = self.parser.parse_args(format_old_style_args)
        warn_string = create_warn_string(args)

        self.assertEqual('rst', args.format)
        self.assertIn('deprecated', warn_string)

        format_old_style_args = ['--format-confluence']
        args = self.parser.parse_args(format_old_style_args)
        warn_string = create_warn_string(args)

        self.assertEqual('confluence', args.format)
        self.assertIn('deprecated', warn_string)

        format_old_style_args = ['--format-html']
        args = self.parser.parse_args(format_old_style_args)
        warn_string = create_warn_string(args)

        self.assertEqual('html', args.format)
        self.assertIn('deprecated', warn_string)

        format_old_style_args = ['--format-json']
        args = self.parser.parse_args(format_old_style_args)
        warn_string = create_warn_string(args)

        self.assertEqual('json', args.format)
        self.assertIn('deprecated', warn_string)

    def test_summary(self):
        summary_args = ['--summary']
        args = self.parser.parse_args(summary_args)
        output_string = create_output_string(args)

        self.assertIn('Count', output_string)
        self.assertNotIn('Name', output_string)

        warn_string = create_warn_string(args)
        self.assertTrue(len(warn_string) == 0)

    def test_summary_sort_by_count(self):
        summary_args = ['--summary', '--order=count']
        args = self.parser.parse_args(summary_args)

        sortby = get_sortby(args)
        self.assertEqual('Count', sortby)

    def test_summary_sort_by_name(self):
        summary_args = ['--summary', '--order=name']
        args = self.parser.parse_args(summary_args)

        sortby = get_sortby(args)
        self.assertEqual('License', sortby)

    def test_summary_warning(self):
        summary_args = ['--summary', '--with-authors']
        args = self.parser.parse_args(summary_args)

        warn_string = create_warn_string(args)
        self.assertIn('using --with-authors and --with-urls will be ignored.',
                      warn_string)

        summary_args = ['--summary', '--with-urls']
        args = self.parser.parse_args(summary_args)

        warn_string = create_warn_string(args)
        self.assertIn('using --with-authors and --with-urls will be ignored.',
                      warn_string)

    def test_output_colored_normal(self):
        color_code = '32'
        text = __pkgname__
        actual = output_colored(color_code, text)

        self.assertTrue(actual.startswith('\033[32'))
        self.assertIn(text, actual)
        self.assertTrue(actual.endswith('\033[0m'))

    def test_output_colored_bold(self):
        color_code = '32'
        text = __pkgname__
        actual = output_colored(color_code, text, is_bold=True)

        self.assertTrue(actual.startswith('\033[1;32'))
        self.assertIn(text, actual)
        self.assertTrue(actual.endswith('\033[0m'))

    def tearDown(self):
        pass
