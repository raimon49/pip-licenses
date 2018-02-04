from __future__ import (division, print_function,
                        absolute_import, unicode_literals)
import unittest

from piplicenses import get_licenses_table, create_parser


class CommandLineTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = create_parser()


class TestGetLicenses(CommandLineTestCase):
    def test_with_empty_args(self):
        empty_args = []
        args = self.parser.parse_args(empty_args)
        table = get_licenses_table(args)
        self.assertTrue(True)  # TODO implementation
