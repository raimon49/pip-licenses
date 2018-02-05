from __future__ import (division, print_function,
                        absolute_import, unicode_literals)
import unittest

from piplicenses import (__pkgname__, create_parser,
                         get_licenses_table, get_output_fields, get_sortby,
                         DEFAULT_OUTPUT_FIELDS, SYSTEM_PACKAGES)


class CommandLineTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = create_parser()


class TestGetLicenses(CommandLineTestCase):
    def setUp(self):
        pass

    def _create_pkg_name_columns(self, table):
        import copy
        # XXX: access to private API
        rows = copy.deepcopy(table._rows)
        pkg_name_columns = []
        for row in rows:
            pkg_name_columns.append(row[0])

        return pkg_name_columns

    def test_with_empty_args(self):
        empty_args = []
        args = self.parser.parse_args(empty_args)
        table = get_licenses_table(args)

        output_fields = get_output_fields(args)
        self.assertEquals(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertNotIn('Author', output_fields)
        self.assertNotIn('URL', output_fields)

        pkg_name_columns = self._create_pkg_name_columns(table)
        for sys_pkg in SYSTEM_PACKAGES:
            self.assertNotIn(sys_pkg, pkg_name_columns)

        sortby = get_sortby(args)
        self.assertEquals('Name', sortby)

    def test_with_system_args(self):
        with_system_args = ['--with-system']
        args = self.parser.parse_args(with_system_args)
        table = get_licenses_table(args)

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

    def tearDown(self):
        pass
