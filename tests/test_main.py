from typing import Sequence

import pytest

from piplicenses.__main__ import get_packages, get_sortby
from piplicenses.argparse import CompatibleArgumentParser

from .conftest import UNICODE_APPENDIX


@pytest.mark.parametrize('order_args,field_name', [
    (['--order=name'], 'Name'),
    (['--order=license'], 'License'),
    (['--order=author', '--with-authors'], 'Author'),
    (['--order=url', '--with-urls'], 'URL'),
    (['--order=url'], 'Name'),
    (['--summary', '--order=count'], 'Count'),
    (['--summary', '--order=name'], 'License'),
])
def test_order(parser: CompatibleArgumentParser,
               order_args: Sequence[str], field_name: str):
    args = parser.parse_args(order_args)
    assert get_sortby(args) == field_name


def test_without_filter(parser: CompatibleArgumentParser):
    args = parser.parse_args([])
    packages = list(get_packages(args))
    assert UNICODE_APPENDIX in packages[-1]["name"]


def test_with_default_filter(parser: CompatibleArgumentParser):
    args = parser.parse_args(["--filter-strings"])
    packages = list(get_packages(args))
    assert UNICODE_APPENDIX not in packages[-1]["name"]


def test_with_specified_filter(parser: CompatibleArgumentParser):
    args = parser.parse_args(["--filter-strings", "--filter-code-page=ascii"])
    packages = list(get_packages(args))
    assert UNICODE_APPENDIX not in packages[-1]["summary"]
