import copy
import re

import docutils.frontend
import docutils.parsers.rst
import docutils.utils
import pytest
from _pytest.capture import CaptureFixture

from piplicenses.__main__ import (
    create_licenses_table, create_output_string, get_output_fields,
    get_sortby)
from piplicenses.argparse import CompatibleArgumentParser
from piplicenses.const import (
    DEFAULT_OUTPUT_FIELDS, SYSTEM_PACKAGES, __pkgname__)
from piplicenses.table import (
    RULE_ALL, RULE_FRAME, RULE_HEADER, RULE_NONE)
from piplicenses.utils import create_warn_string


def _create_pkg_name_columns(table):
    index = DEFAULT_OUTPUT_FIELDS.index('Name')

    # XXX: access to private API
    rows = copy.deepcopy(table._rows)
    pkg_name_columns = []
    for row in rows:
        pkg_name_columns.append(row[index])

    return pkg_name_columns


def _create_license_columns(table, output_fields):
    index = output_fields.index('License')

    # XXX: access to private API
    rows = copy.deepcopy(table._rows)
    pkg_name_columns = []
    for row in rows:
        pkg_name_columns.append(row[index])

    return pkg_name_columns


# from https://stackoverflow.com/questions/12883428/ ...
# ... how-to-parse-restructuredtext-in-python
def _check_rst(text: str):
    parser = docutils.parsers.rst.Parser()
    components = (docutils.parsers.rst.Parser,)
    settings = docutils.frontend.\
        OptionParser(components=components).get_default_values()
    settings.halt_level = 3
    document = docutils.utils.new_document('<rst-doc>', settings=settings)
    parser.parse(text, document)


def test_with_empty_args(parser: CompatibleArgumentParser):
    empty_args = []
    args = parser.parse_args(empty_args)
    table = create_licenses_table(args)

    assert 'l' in table.align.values()
    assert table.border is False
    assert table.header is True
    assert table.junction_char == '+'
    assert table.hrules == RULE_FRAME

    output_fields = get_output_fields(args)
    assert output_fields == list(DEFAULT_OUTPUT_FIELDS) + ['License']
    assert 'Author' not in output_fields
    assert 'URL' not in output_fields

    pkg_name_columns = _create_pkg_name_columns(table)
    for sys_pkg in SYSTEM_PACKAGES:
        assert sys_pkg not in pkg_name_columns

    assert get_sortby(args) == 'Name'

    output_string = create_output_string(args)
    assert '<table>' not in output_string


def test_from_meta(parser: CompatibleArgumentParser):
    from_args = ['--from=meta']
    args = parser.parse_args(from_args)

    output_fields = get_output_fields(args)
    assert 'License' in output_fields

    table = create_licenses_table(args, output_fields)
    license_columns = _create_license_columns(table, output_fields)
    license_notation_as_meta = 'BSD-3-Clause'
    assert license_notation_as_meta in license_columns


def test_from_classifier(parser: CompatibleArgumentParser):
    from_args = ['--from=classifier']
    args = parser.parse_args(from_args)
    output_fields = get_output_fields(args)
    table = create_licenses_table(args, output_fields)

    assert 'License' in output_fields

    license_columns = _create_license_columns(table, output_fields)
    license_notation_as_classifier = 'MIT License'
    assert license_notation_as_classifier in license_columns


def test_from_mixed(parser: CompatibleArgumentParser):
    from_args = ['--from=mixed']
    args = parser.parse_args(from_args)
    output_fields = get_output_fields(args)
    table = create_licenses_table(args, output_fields)

    assert 'License' in output_fields

    license_columns = _create_license_columns(table, output_fields)
    # Depending on the condition "MIT" or "BSD" etc.
    license_notation_as_classifier = 'MIT License'
    assert license_notation_as_classifier in license_columns


def test_from_all(parser: CompatibleArgumentParser):
    from_args = ['--from=all']
    args = parser.parse_args(from_args)
    output_fields = get_output_fields(args)
    table = create_licenses_table(args, output_fields)

    assert 'License-Metadata' in output_fields
    assert 'License-Classifier' in output_fields

    index_license_meta = output_fields.index('License-Metadata')
    license_meta = []
    for row in table._rows:
        license_meta.append(row[index_license_meta])

    index_license_classifier = output_fields.index('License-Classifier')
    license_classifier = []
    for row in table._rows:
        license_classifier.append(row[index_license_classifier])

    for license in ('BSD', 'MIT', 'Apache 2.0'):
        assert license in license_meta
    for license in ('BSD License', 'MIT License',
                    'Apache Software License'):
        assert license in license_classifier


def test_with_system(parser: CompatibleArgumentParser):
    with_system_args = ['--with-system']
    args = parser.parse_args(with_system_args)
    table = create_licenses_table(args)

    pkg_name_columns = _create_pkg_name_columns(table)
    external_sys_pkgs = list(SYSTEM_PACKAGES)
    external_sys_pkgs.remove(__pkgname__)
    for sys_pkg in external_sys_pkgs:
        assert sys_pkg in pkg_name_columns


def test_with_authors(parser: CompatibleArgumentParser):
    with_authors_args = ['--with-authors']
    args = parser.parse_args(with_authors_args)

    output_fields = get_output_fields(args)
    assert output_fields != list(DEFAULT_OUTPUT_FIELDS)
    assert 'Author' in output_fields

    output_string = create_output_string(args)
    assert 'Author' in output_string


def test_with_urls(parser: CompatibleArgumentParser):
    with_urls_args = ['--with-urls']
    args = parser.parse_args(with_urls_args)

    output_fields = get_output_fields(args)
    assert output_fields != list(DEFAULT_OUTPUT_FIELDS)
    assert 'URL' in output_fields

    output_string = create_output_string(args)
    assert 'URL' in output_string


def test_with_description(parser: CompatibleArgumentParser):
    with_description_args = ['--with-description']
    args = parser.parse_args(with_description_args)

    output_fields = get_output_fields(args)
    assert output_fields != list(DEFAULT_OUTPUT_FIELDS)
    assert 'Description' in output_fields

    output_string = create_output_string(args)
    assert 'Description' in output_string


def test_with_license_file(parser: CompatibleArgumentParser):
    with_license_file_args = ['--with-license-file']
    args = parser.parse_args(with_license_file_args)

    output_fields = get_output_fields(args)
    assert output_fields != list(DEFAULT_OUTPUT_FIELDS)
    assert 'LicenseFile' in output_fields
    assert 'LicenseText' in output_fields
    assert 'NoticeFile' not in output_fields
    assert 'NoticeText' not in output_fields

    output_string = create_output_string(args)
    assert 'LicenseFile' in output_string
    assert 'LicenseText' in output_string
    assert 'NoticeFile' not in output_string
    assert 'NoticeText' not in output_string


def test_with_notice_file(parser: CompatibleArgumentParser):
    with_license_file_args = ['--with-license-file', '--with-notice-file']
    args = parser.parse_args(with_license_file_args)

    output_fields = get_output_fields(args)
    assert output_fields != list(DEFAULT_OUTPUT_FIELDS)
    assert 'LicenseFile' in output_fields
    assert 'LicenseText' in output_fields
    assert 'NoticeFile' in output_fields
    assert 'NoticeText' in output_fields

    output_string = create_output_string(args)
    assert 'LicenseFile' in output_string
    assert 'LicenseText' in output_string
    assert 'NoticeFile' in output_string
    assert 'NoticeText' in output_string


def test_with_license_file_no_path(parser: CompatibleArgumentParser):
    with_license_file_args = ['--with-license-file', '--with-notice-file',
                              '--no-license-path']
    args = parser.parse_args(with_license_file_args)

    output_fields = get_output_fields(args)
    assert output_fields != list(DEFAULT_OUTPUT_FIELDS)
    assert 'LicenseFile' not in output_fields
    assert 'LicenseText' in output_fields
    assert 'NoticeFile' not in output_fields
    assert 'NoticeText' in output_fields

    output_string = create_output_string(args)
    assert 'LicenseFile' not in output_string
    assert 'LicenseText' in output_string
    assert 'NoticeFile' not in output_string
    assert 'NoticeText' in output_string


def test_ignore_packages(parser: CompatibleArgumentParser):
    if 'PTable' in SYSTEM_PACKAGES:
        ignore_pkg_name = 'PTable'
    else:
        ignore_pkg_name = 'prettytable'
    ignore_packages_args = ['--ignore-package=' + ignore_pkg_name]
    args = parser.parse_args(ignore_packages_args)
    table = create_licenses_table(args)

    pkg_name_columns = _create_pkg_name_columns(table)
    assert ignore_pkg_name not in pkg_name_columns


def test_format_plain_vertical(parser: CompatibleArgumentParser):
    format_plain_args = ['--format=plain-vertical', '--from=classifier']
    args = parser.parse_args(format_plain_args)
    output_string = create_output_string(args)
    assert re.search(r'pytest\n\d\.\d\.\d\nMIT License\n', output_string) \
        is not None


def test_format_markdown(parser: CompatibleArgumentParser):
    format_markdown_args = ['--format=markdown']
    args = parser.parse_args(format_markdown_args)
    table = create_licenses_table(args)

    assert 'l' in table.align.values()
    assert table.border is True
    assert table.header is True
    assert table.junction_char == '|'
    assert table.hrules == RULE_HEADER


def test_format_rst_without_filter(parser: CompatibleArgumentParser):
    format_rst_args = ['--format=rst']
    args = parser.parse_args(format_rst_args)
    table = create_licenses_table(args)

    assert 'l' in table.align.values()
    assert table.border is True
    assert table.header is True
    assert table.junction_char == '+'
    assert table.hrules == RULE_ALL
    with pytest.raises(docutils.utils.SystemMessage):
        _check_rst(str(table))


def test_format_rst_default_filter(parser: CompatibleArgumentParser):
    format_rst_args = ['--format=rst', '--filter-strings']
    args = parser.parse_args(format_rst_args)
    table = create_licenses_table(args)

    assert 'l' in table.align.values()
    assert table.border is True
    assert table.header is True
    assert table.junction_char == '+'
    assert table.hrules == RULE_ALL
    _check_rst(str(table))


def test_format_confluence(parser: CompatibleArgumentParser):
    format_confluence_args = ['--format=confluence']
    args = parser.parse_args(format_confluence_args)
    table = create_licenses_table(args)

    assert 'l' in table.align.values()
    assert table.border is True
    assert table.header is True
    assert table.junction_char == '|'
    assert table.hrules == RULE_NONE


def test_format_html(parser: CompatibleArgumentParser):
    format_html_args = ['--format=html']
    args = parser.parse_args(format_html_args)
    output_string = create_output_string(args)

    assert '<table>' in output_string


def test_format_json(parser: CompatibleArgumentParser):
    format_json_args = ['--format=json', '--with-authors']
    args = parser.parse_args(format_json_args)
    output_string = create_output_string(args)

    assert '"Author":' in output_string
    assert '"URL":' not in output_string


def test_format_json_license_manager(parser: CompatibleArgumentParser):
    format_json_args = ['--format=json-license-finder']
    args = parser.parse_args(format_json_args)
    output_string = create_output_string(args)

    assert '"URL":' not in output_string
    assert '"name":' in output_string
    assert '"version":' in output_string
    assert '"licenses":' in output_string


def test_format_csv(parser: CompatibleArgumentParser):
    format_csv_args = ['--format=csv', '--with-authors']
    args = parser.parse_args(format_csv_args)
    output_string = create_output_string(args)

    obtained_header = output_string.split('\n', 1)[0]
    expected_header = '"Name","Version","License","Author"'
    assert obtained_header == expected_header


def test_summary(parser: CompatibleArgumentParser):
    summary_args = ['--summary']
    args = parser.parse_args(summary_args)
    output_string = create_output_string(args)

    assert 'Count' in output_string
    assert 'Name' not in output_string

    warn_string = create_warn_string(args)
    assert len(warn_string) == 0


def test_allow_only(parser: CompatibleArgumentParser, capsys: CaptureFixture):
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
    args = parser.parse_args(allow_only_args)
    with pytest.raises(SystemExit) as ex:
        create_licenses_table(args)
    assert ex.value.code == 1

    capture = capsys.readouterr()
    assert capture.out == ''
    assert 'license MIT License not in allow-only licenses was found for ' \
           'package' in capture.err


def test_fail_on(parser: CompatibleArgumentParser, capsys: CaptureFixture):
    licenses = (
        "MIT License",
    )
    allow_only_args = ['--fail-on={}'.format(";".join(licenses))]
    args = parser.parse_args(allow_only_args)
    with pytest.raises(SystemExit) as ex:
        create_licenses_table(args)
    assert ex.value.code == 1

    capture = capsys.readouterr()
    assert capture.out == ''
    assert 'fail-on license MIT License was found for ' \
           'package' in capture.err
