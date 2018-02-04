from __future__ import (division, print_function,
                        absolute_import, unicode_literals)
import unittest

from piplicenses import get_licenses, create_parser


class CommandLineTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = create_parser()


class TestGetLicenses(CommandLineTestCase):
    def test_with_empty_args(self):
        empty_args = []
        args = self.parser.parse_args(empty_args)
        licenses = get_licenses(args.with_system,
                                args.with_authors,
                                args.with_urls)
        self.assertTrue(True)  # TODO implementation
