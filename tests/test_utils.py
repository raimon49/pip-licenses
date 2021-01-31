import sys
from enum import Enum, auto
from unittest.mock import Mock, mock_open, patch

import pytest
from _pytest.capture import CaptureFixture

from piplicenses.argparse import CompatibleArgumentParser
from piplicenses.const import __pkgname__
from piplicenses.utils import (
    create_warn_string, enum_key_to_value, output_colored,
    save_if_needs, value_to_enum_key)


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


def test_with_license_file_warning(parser: CompatibleArgumentParser):
    with_license_file_args = ['--with-license-file', '--format=markdown']
    args = parser.parse_args(with_license_file_args)

    warn_string = create_warn_string(args)
    assert 'best paired with --format=json' in warn_string


def test_summary_warning(parser: CompatibleArgumentParser):
    summary_args = ['--summary', '--with-authors']
    args = parser.parse_args(summary_args)

    warn_string = create_warn_string(args)
    assert 'using --with-authors and --with-urls will be ignored.' \
        in warn_string

    summary_args = ['--summary', '--with-urls']
    args = parser.parse_args(summary_args)

    warn_string = create_warn_string(args)
    assert 'using --with-authors and --with-urls will be ignored.' \
        in warn_string


def test_output_colored_normal():
    color_code = '32'
    text = __pkgname__
    actual = output_colored(color_code, text)

    assert actual.startswith('\033[32') is True
    assert text in actual
    assert actual.endswith('\033[0m') is True


def test_output_colored_bold():
    color_code = '32'
    text = __pkgname__
    actual = output_colored(color_code, text, is_bold=True)

    assert actual.startswith('\033[1;32') is True
    assert text in actual
    assert actual.endswith('\033[0m') is True


def test_output_file_success(capsys: CaptureFixture):
    mock_file = mock_open()
    with patch('builtins.open', mock_file):
        with pytest.raises(SystemExit) as ex:
            save_if_needs('/foo/bar.txt', 'license list')
        mock_file.assert_called_once_with('/foo/bar.txt', 'w',
                                          encoding='utf-8')
        handle: Mock = mock_file()
        handle.write.assert_called_once_with('license list')
    assert ex.value.code == 0
    capture = capsys.readouterr()
    assert 'created path: ' in capture.out
    assert capture.err == ''


def test_output_file_error(capsys: CaptureFixture):
    mock_file: Mock = mock_open()
    with patch('builtins.open', mock_file):
        mock_file.side_effect = [IOError]
        with pytest.raises(SystemExit) as ex:
            save_if_needs('/foo/bar.txt', 'license list')
        mock_file.assert_called_once_with('/foo/bar.txt', 'w',
                                          encoding='utf-8')
    assert ex.value.code == 1
    capture = capsys.readouterr()
    assert capture.out == ''
    assert 'check path: ' in capture.err


def test_output_file_none(capsys: CaptureFixture):
    assert save_if_needs(None, 'license list') is None
    # stdout and stderr are expected not to be called
    capture = capsys.readouterr()
    assert capture.out == ''
    assert capture.err == ''
