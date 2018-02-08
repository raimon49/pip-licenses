from __future__ import (division, print_function,
                        absolute_import, unicode_literals)
import unittest
from email import message_from_string

from piplicenses import (__pkgname__, create_parser,
                         create_licenses_table, get_output_fields, get_sortby,
                         find_license_from_classifier,
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

        output_fields = get_output_fields(args)
        self.assertEquals(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertNotIn('Author', output_fields)
        self.assertNotIn('URL', output_fields)

        pkg_name_columns = self._create_pkg_name_columns(table)
        for sys_pkg in SYSTEM_PACKAGES:
            self.assertNotIn(sys_pkg, pkg_name_columns)

        sortby = get_sortby(args)
        self.assertEquals('Name', sortby)

    def test_from_classifier(self):
        from_classifier_args = ['--from-classifier']
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
        self.assertEquals('MIT License',
                          find_license_from_classifier(message))

    def test_not_fond_license_from_classifier(self):
        metadata_as_no_license = ('Metadata-Version: 2.0\r\n'
                                  'Name: pip-licenses\r\n'
                                  'Version: 1.0.0\r\n')
        message = message_from_string(metadata_as_no_license)
        self.assertEquals(LICENSE_UNKNOWN,
                          find_license_from_classifier(message))

    def test_with_system_args(self):
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
        self.assertNotEquals(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn('Author', output_fields)

    def test_with_urls(self):
        with_urls_args = ['--with-urls']
        args = self.parser.parse_args(with_urls_args)

        output_fields = get_output_fields(args)
        self.assertNotEquals(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn('URL', output_fields)

    def test_order_name(self):
        order_name_args = ['--order=name']
        args = self.parser.parse_args(order_name_args)

        sortby = get_sortby(args)
        self.assertEquals('Name', sortby)

    def test_order_license(self):
        order_license_args = ['--order=license']
        args = self.parser.parse_args(order_license_args)

        sortby = get_sortby(args)
        self.assertEquals('License', sortby)

    def test_order_author(self):
        order_author_args = ['--order=author', '--with-authors']
        args = self.parser.parse_args(order_author_args)

        sortby = get_sortby(args)
        self.assertEquals('Author', sortby)

    def test_order_url(self):
        order_url_args = ['--order=url', '--with-urls']
        args = self.parser.parse_args(order_url_args)

        sortby = get_sortby(args)
        self.assertEquals('URL', sortby)

    def test_order_url_no_effect(self):
        order_url_args = ['--order=url']
        args = self.parser.parse_args(order_url_args)

        sortby = get_sortby(args)
        self.assertEquals('Name', sortby)

    def tearDown(self):
        pass
