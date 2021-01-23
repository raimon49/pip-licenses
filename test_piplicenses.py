# -*- coding: utf-8 -*-
# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et
import copy
import re
import sys
import unittest
from email import message_from_string
from enum import Enum, auto

import docutils.frontend
import docutils.parsers.rst
import docutils.utils
import pytest
from _pytest.capture import CaptureFixture

import piplicenses
from piplicenses import (
    DEFAULT_OUTPUT_FIELDS, LICENSE_UNKNOWN, RULE_ALL, RULE_FRAME,
    RULE_HEADER, RULE_NONE, SYSTEM_PACKAGES, CompatibleArgumentParser,
    FromArg, __pkgname__, create_licenses_table, create_output_string,
    create_parser, create_warn_string, enum_key_to_value,
    factory_styled_table_with_args, find_license_from_classifier,
    get_output_fields, get_sortby, output_colored, save_if_needs,
    select_license_by_source, value_to_enum_key)

UNICODE_APPENDIX = ""
with open('tests/fixtures/unicode_characters.txt', encoding='utf-8') as f:
    # Read from external file considering a terminal that cannot handle "emoji"
    UNICODE_APPENDIX = f.readline().replace("\n", "")


def get_installed_distributions_mocked(*args, **kwargs):
    packages = get_installed_distributions_orig(*args, **kwargs)
    if not packages[-1].project_name.endswith(UNICODE_APPENDIX):
        packages[-1].project_name += " "+UNICODE_APPENDIX
    return packages


get_installed_distributions_orig = piplicenses.get_installed_distributions
piplicenses.get_installed_distributions = get_installed_distributions_mocked


class CommandLineTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = create_parser()


class TestGetLicenses(CommandLineTestCase):

    def _create_pkg_name_columns(self, table):
        index = DEFAULT_OUTPUT_FIELDS.index('Name')

        # XXX: access to private API
        rows = copy.deepcopy(table._rows)
        pkg_name_columns = []
        for row in rows:
            pkg_name_columns.append(row[index])

        return pkg_name_columns

    def _create_license_columns(self, table, output_fields):
        index = output_fields.index('License')

        # XXX: access to private API
        rows = copy.deepcopy(table._rows)
        pkg_name_columns = []
        for row in rows:
            pkg_name_columns.append(row[index])

        return pkg_name_columns

    # from https://stackoverflow.com/questions/12883428/ ...
    # ... how-to-parse-restructuredtext-in-python
    @staticmethod
    def check_rst(text: str):
        parser = docutils.parsers.rst.Parser()
        components = (docutils.parsers.rst.Parser,)
        settings = docutils.frontend.\
            OptionParser(components=components).get_default_values()
        settings.halt_level = 3
        document = docutils.utils.new_document('<rst-doc>', settings=settings)
        parser.parse(text, document)

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
        self.assertEqual(output_fields,
                         list(DEFAULT_OUTPUT_FIELDS) + ['License'])
        self.assertNotIn('Author', output_fields)
        self.assertNotIn('URL', output_fields)

        pkg_name_columns = self._create_pkg_name_columns(table)
        for sys_pkg in SYSTEM_PACKAGES:
            self.assertNotIn(sys_pkg, pkg_name_columns)

        sortby = get_sortby(args)
        self.assertEqual('Name', sortby)

        output_string = create_output_string(args)
        self.assertNotIn('<table>', output_string)

    def test_from_meta(self):
        from_args = ['--from=meta']
        args = self.parser.parse_args(from_args)

        output_fields = get_output_fields(args)
        self.assertIn('License', output_fields)

        table = create_licenses_table(args, output_fields)
        license_columns = self._create_license_columns(table, output_fields)
        license_notation_as_meta = 'BSD-3-Clause'
        self.assertIn(license_notation_as_meta, license_columns)

    def test_from_classifier(self):
        from_args = ['--from=classifier']
        args = self.parser.parse_args(from_args)
        output_fields = get_output_fields(args)
        table = create_licenses_table(args, output_fields)

        self.assertIn('License', output_fields)

        license_columns = self._create_license_columns(table, output_fields)
        license_notation_as_classifier = 'MIT License'
        self.assertIn(license_notation_as_classifier, license_columns)

    def test_from_mixed(self):
        from_args = ['--from=mixed']
        args = self.parser.parse_args(from_args)
        output_fields = get_output_fields(args)
        table = create_licenses_table(args, output_fields)

        self.assertIn('License', output_fields)

        license_columns = self._create_license_columns(table, output_fields)
        # Depending on the condition "MIT" or "BSD" etc.
        license_notation_as_classifier = 'MIT License'
        self.assertIn(license_notation_as_classifier, license_columns)

    def test_from_all(self):
        from_args = ['--from=all']
        args = self.parser.parse_args(from_args)
        output_fields = get_output_fields(args)
        table = create_licenses_table(args, output_fields)

        self.assertIn('License-Metadata', output_fields)
        self.assertIn('License-Classifier', output_fields)

        index_license_meta = output_fields.index('License-Metadata')
        license_meta = []
        for row in table._rows:
            license_meta.append(row[index_license_meta])

        index_license_classifier = output_fields.index('License-Classifier')
        license_classifier = []
        for row in table._rows:
            license_classifier.append(row[index_license_classifier])

        for license in ('BSD', 'MIT', 'Apache 2.0'):
            self.assertIn(license, license_meta)
        for license in ('BSD License', 'MIT License',
                        'Apache Software License'):
            self.assertIn(license, license_classifier)

    def test_find_license_from_classifier(self):
        metadata = ('Metadata-Version: 2.0\r\n'
                    'Name: pip-licenses\r\n'
                    'Version: 1.0.0\r\n'
                    'Classifier: License :: OSI Approved :: MIT License\r\n')
        message = message_from_string(metadata)
        self.assertEqual(['MIT License'],
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
        self.assertEqual(['GNU General Public License v3 (GPLv3)',
                          'MIT License',
                          'Public Domain'],
                         find_license_from_classifier(message))

    def test_not_found_license_from_classifier(self):
        metadata_as_no_license = ('Metadata-Version: 2.0\r\n'
                                  'Name: pip-licenses\r\n'
                                  'Version: 1.0.0\r\n')
        message = message_from_string(metadata_as_no_license)
        self.assertEqual([],
                         find_license_from_classifier(message))

    def test_select_license_by_source(self):
        self.assertEqual('MIT License',
                         select_license_by_source(FromArg.CLASSIFIER,
                                                  ['MIT License'],
                                                  'MIT'))

        self.assertEqual(LICENSE_UNKNOWN,
                         select_license_by_source(FromArg.CLASSIFIER,
                                                  [],
                                                  'MIT'))

        self.assertEqual('MIT License',
                         select_license_by_source(FromArg.MIXED,
                                                  ['MIT License'],
                                                  'MIT'))

        self.assertEqual('MIT',
                         select_license_by_source(FromArg.MIXED,
                                                  [],
                                                  'MIT'))

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
        self.assertNotIn('NoticeFile', output_fields)
        self.assertNotIn('NoticeText', output_fields)

        output_string = create_output_string(args)
        self.assertIn('LicenseFile', output_string)
        self.assertIn('LicenseText', output_string)
        self.assertNotIn('NoticeFile', output_string)
        self.assertNotIn('NoticeText', output_string)

    def test_with_notice_file(self):
        with_license_file_args = ['--with-license-file', '--with-notice-file']
        args = self.parser.parse_args(with_license_file_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn('LicenseFile', output_fields)
        self.assertIn('LicenseText', output_fields)
        self.assertIn('NoticeFile', output_fields)
        self.assertIn('NoticeText', output_fields)

        output_string = create_output_string(args)
        self.assertIn('LicenseFile', output_string)
        self.assertIn('LicenseText', output_string)
        self.assertIn('NoticeFile', output_string)
        self.assertIn('NoticeText', output_string)

    def test_with_license_file_no_path(self):
        with_license_file_args = ['--with-license-file', '--with-notice-file',
                                  '--no-license-path']
        args = self.parser.parse_args(with_license_file_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertNotIn('LicenseFile', output_fields)
        self.assertIn('LicenseText', output_fields)
        self.assertNotIn('NoticeFile', output_fields)
        self.assertIn('NoticeText', output_fields)

        output_string = create_output_string(args)
        self.assertNotIn('LicenseFile', output_string)
        self.assertIn('LicenseText', output_string)
        self.assertNotIn('NoticeFile', output_string)
        self.assertIn('NoticeText', output_string)

    def test_with_license_file_warning(self):
        with_license_file_args = ['--with-license-file', '--format=markdown']
        args = self.parser.parse_args(with_license_file_args)

        warn_string = create_warn_string(args)
        self.assertIn('best paired with --format=json', warn_string)

    def test_ignore_packages(self):
        if 'PTable' in SYSTEM_PACKAGES:
            ignore_pkg_name = 'PTable'
        else:
            ignore_pkg_name = 'prettytable'
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

    def test_format_plain_vertical(self):
        format_plain_args = ['--format=plain-vertical', '--from=classifier']
        args = self.parser.parse_args(format_plain_args)
        output_string = create_output_string(args)
        self.assertIsNotNone(
            re.search(r'pytest\n\d\.\d\.\d\nMIT License\n', output_string))

    def test_format_markdown(self):
        format_markdown_args = ['--format=markdown']
        args = self.parser.parse_args(format_markdown_args)
        table = create_licenses_table(args)

        self.assertIn('l', table.align.values())
        self.assertTrue(table.border)
        self.assertTrue(table.header)
        self.assertEqual('|', table.junction_char)
        self.assertEqual(RULE_HEADER, table.hrules)

    @unittest.skipIf(sys.version_info < (3, 6, 0),
                     "To unsupport Python 3.5 in the near future")
    def test_format_rst_without_filter(self):
        format_rst_args = ['--format=rst']
        args = self.parser.parse_args(format_rst_args)
        table = create_licenses_table(args)

        self.assertIn('l', table.align.values())
        self.assertTrue(table.border)
        self.assertTrue(table.header)
        self.assertEqual('+', table.junction_char)
        self.assertEqual(RULE_ALL, table.hrules)
        with self.assertRaises(docutils.utils.SystemMessage):
            self.check_rst(str(table))

    def test_format_rst_default_filter(self):
        format_rst_args = ['--format=rst', '--filter-strings']
        args = self.parser.parse_args(format_rst_args)
        table = create_licenses_table(args)

        self.assertIn('l', table.align.values())
        self.assertTrue(table.border)
        self.assertTrue(table.header)
        self.assertEqual('+', table.junction_char)
        self.assertEqual(RULE_ALL, table.hrules)
        self.check_rst(str(table))

    def test_format_confluence(self):
        format_confluence_args = ['--format=confluence']
        args = self.parser.parse_args(format_confluence_args)
        table = create_licenses_table(args)

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

    def test_format_json_license_manager(self):
        format_json_args = ['--format=json-license-finder']
        args = self.parser.parse_args(format_json_args)
        output_string = create_output_string(args)

        self.assertNotIn('"URL":', output_string)
        self.assertIn('"name":', output_string)
        self.assertIn('"version":', output_string)
        self.assertIn('"licenses":', output_string)

    def test_format_csv(self):
        format_csv_args = ['--format=csv', '--with-authors']
        args = self.parser.parse_args(format_csv_args)
        output_string = create_output_string(args)

        obtained_header = output_string.split('\n', 1)[0]
        expected_header = '"Name","Version","License","Author"'
        self.assertEqual(obtained_header, expected_header)

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

    def test_without_filter(self):
        args = self.parser.parse_args([])
        packages = list(piplicenses.get_packages(args))
        self.assertIn(UNICODE_APPENDIX, packages[-1]["name"])

    def test_with_default_filter(self):
        args = self.parser.parse_args(["--filter-strings"])
        packages = list(piplicenses.get_packages(args))
        self.assertNotIn(UNICODE_APPENDIX, packages[-1]["name"])

    def test_with_specified_filter(self):
        args = self.parser.parse_args(["--filter-strings",
                                       "--filter-code-page=ascii"])
        packages = list(piplicenses.get_packages(args))
        self.assertNotIn(UNICODE_APPENDIX, packages[-1]["summary"])


class MockStdStream(object):

    def __init__(self):
        self.printed = ''

    def write(self, p):
        self.printed = p


def test_output_file_sccess(monkeypatch):
    def mocked_open(*args, **kwargs):
        import tempfile
        return tempfile.TemporaryFile('w')

    mocked_stdout = MockStdStream()
    mocked_stderr = MockStdStream()
    monkeypatch.setattr(piplicenses, 'open', mocked_open)
    monkeypatch.setattr(sys.stdout, 'write', mocked_stdout.write)
    monkeypatch.setattr(sys.stderr, 'write', mocked_stderr.write)
    monkeypatch.setattr(sys, 'exit', lambda n: None)

    save_if_needs('/foo/bar.txt', 'license list')
    assert 'created path: ' in mocked_stdout.printed
    assert '' == mocked_stderr.printed


def test_output_file_error(monkeypatch):
    def mocked_open(*args, **kwargs):
        raise IOError

    mocked_stdout = MockStdStream()
    mocked_stderr = MockStdStream()
    monkeypatch.setattr(piplicenses, 'open', mocked_open)
    monkeypatch.setattr(sys.stdout, 'write', mocked_stdout.write)
    monkeypatch.setattr(sys.stderr, 'write', mocked_stderr.write)
    monkeypatch.setattr(sys, 'exit', lambda n: None)

    save_if_needs('/foo/bar.txt', 'license list')
    assert '' == mocked_stdout.printed
    assert 'check path: ' in mocked_stderr.printed


def test_output_file_none(monkeypatch):
    mocked_stdout = MockStdStream()
    mocked_stderr = MockStdStream()
    monkeypatch.setattr(sys.stdout, 'write', mocked_stdout.write)
    monkeypatch.setattr(sys.stderr, 'write', mocked_stderr.write)

    save_if_needs(None, 'license list')
    # stdout and stderr are expected not to be called
    assert '' == mocked_stdout.printed
    assert '' == mocked_stderr.printed


def test_allow_only(monkeypatch):
    licenses = (
        "BSD License",
        "Apache Software License",
        "Mozilla Public License 2.0 (MPL 2.0)",
        "MIT License, Mozilla Public License 2.0 (MPL 2.0)",
        "Apache Software License, BSD License",
        "Python Software Foundation License, MIT License",
        "Public Domain, Python Software Foundation License, BSD License,"
        "GNU General Public License (GPL)",
        "GNU Library or Lesser General Public License (LGPL)",
    )
    allow_only_args = ['--allow-only={}'.format(";".join(licenses))]
    mocked_stdout = MockStdStream()
    mocked_stderr = MockStdStream()
    monkeypatch.setattr(sys.stdout, 'write', mocked_stdout.write)
    monkeypatch.setattr(sys.stderr, 'write', mocked_stderr.write)
    monkeypatch.setattr(sys, 'exit', lambda n: None)
    args = create_parser().parse_args(allow_only_args)
    create_licenses_table(args)

    assert '' == mocked_stdout.printed
    assert 'license MIT License not in allow-only licenses was found for ' \
           'package' in mocked_stderr.printed


def test_fail_on(monkeypatch):
    licenses = (
        "MIT License",
    )
    allow_only_args = ['--fail-on={}'.format(";".join(licenses))]
    mocked_stdout = MockStdStream()
    mocked_stderr = MockStdStream()
    monkeypatch.setattr(sys.stdout, 'write', mocked_stdout.write)
    monkeypatch.setattr(sys.stderr, 'write', mocked_stderr.write)
    monkeypatch.setattr(sys, 'exit', lambda n: None)
    args = create_parser().parse_args(allow_only_args)
    create_licenses_table(args)

    assert '' == mocked_stdout.printed
    assert 'fail-on license MIT License was found for ' \
           'package' in mocked_stderr.printed


def test_enums():
    class TestEnum(Enum):
        PLAIN = P = auto()
        JSON_LICENSE_FINDER = JLF = auto()

    assert TestEnum.PLAIN == TestEnum.P
    assert getattr(TestEnum, value_to_enum_key('jlf')) == \
        TestEnum.JSON_LICENSE_FINDER
    assert value_to_enum_key('jlf') == 'JLF'
    assert value_to_enum_key('json-license-finder') == \
        'JSON_LICENSE_FINDER'
    assert enum_key_to_value(TestEnum.JSON_LICENSE_FINDER) == \
        'json-license-finder'
    assert enum_key_to_value(TestEnum.PLAIN) == 'plain'


@pytest.fixture(scope='package')
def parser():
    return create_parser()


def test_verify_args(
        parser: CompatibleArgumentParser, capsys: CaptureFixture):
    # --with-license-file missing
    with pytest.raises(SystemExit) as ex:
        parser.parse_args(['--no-license-path'])
    capture = capsys.readouterr().err
    for arg in ('--no-license-path', '--with-license-file'):
        assert arg in capture

    with pytest.raises(SystemExit) as ex:
        parser.parse_args(['--with-notice-file'])
    capture = capsys.readouterr().err
    for arg in ('--with-notice-file', '--with-license-file'):
        assert arg in capture

    # --filter-strings missing
    with pytest.raises(SystemExit) as ex:
        parser.parse_args(['--filter-code-page=utf8'])
    capture = capsys.readouterr().err
    for arg in ('--filter-code-page', '--filter-strings'):
        assert arg in capture

    # invalid code-page
    with pytest.raises(SystemExit) as ex:
        parser.parse_args(['--filter-strings', '--filter-code-page=XX'])
    capture = capsys.readouterr().err
    for arg in ('invalid code', '--filter-code-page'):
        assert arg in capture
