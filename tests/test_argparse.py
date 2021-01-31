import pytest
from _pytest.capture import CaptureFixture

from piplicenses.argparse import CompatibleArgumentParser


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
