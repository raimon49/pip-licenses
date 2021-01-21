from email import message_from_string
from typing import List

import pytest

from piplicenses.const import LICENSE_UNKNOWN, FromArg
from piplicenses.parse import (
    find_license_from_classifier, select_license_by_source)


def test_find_license_from_classifier():
    metadata = ('Metadata-Version: 2.0\r\n'
                'Name: pip-licenses\r\n'
                'Version: 1.0.0\r\n'
                'Classifier: License :: OSI Approved :: MIT License\r\n')
    message = message_from_string(metadata)
    assert ['MIT License'] == find_license_from_classifier(message)


def test_display_multiple_license_from_classifier():
    metadata = ('Metadata-Version: 2.0\r\n'
                'Name: helga\r\n'
                'Version: 1.7.6\r\n'
                'Classifier: License :: OSI Approved\r\n'
                'Classifier: License :: OSI Approved :: '
                'GNU General Public License v3 (GPLv3)\r\n'
                'Classifier: License :: OSI Approved :: MIT License\r\n'
                'Classifier: License :: Public Domain\r\n')
    message = message_from_string(metadata)
    assert find_license_from_classifier(message) == [
        'GNU General Public License v3 (GPLv3)',
        'MIT License',
        'Public Domain']


def test_not_found_license_from_classifier():
    metadata_as_no_license = ('Metadata-Version: 2.0\r\n'
                              'Name: pip-licenses\r\n'
                              'Version: 1.0.0\r\n')
    message = message_from_string(metadata_as_no_license)
    assert find_license_from_classifier(message) == []


@pytest.mark.parametrize('from_arg,classifier,meta,expected', [
    (FromArg.CLASSIFIER, ['MIT License'], 'MIT', 'MIT License'),
    (FromArg.CLASSIFIER, [], 'MIT', LICENSE_UNKNOWN),
    (FromArg.MIXED, ['MIT License'], 'MIT', 'MIT License'),
    (FromArg.MIXED, [], 'MIT', 'MIT'),
])
def test_select_license_by_source(
        from_arg: FromArg, classifier: List[str], meta: str, expected: str):
    assert select_license_by_source(from_arg, classifier, meta) == expected
