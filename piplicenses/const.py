# ---------------------------------------------------------------------------
# Licensed under the MIT License. See LICENSE file for license information.
# ---------------------------------------------------------------------------
from argparse import Namespace
from enum import Enum, auto
from typing import List, Optional

try:
    from prettytable.prettytable import ALL
    PTABLE = True
except ImportError:  # pragma: no cover
    PTABLE = False


# General information
__pkgname__ = 'pip-licenses'
__version__ = '3.3.0'
__author__ = 'raimon'
__license__ = 'MIT'
__summary__ = ('Dump the software license list of '
               'Python packages installed with pip.')
__url__ = 'https://github.com/raimon49/pip-licenses'


FIELD_NAMES = (
    'Name',
    'Version',
    'License',
    'LicenseFile',
    'LicenseText',
    'NoticeFile',
    'NoticeText',
    'Author',
    'Description',
    'URL',
)
SUMMARY_FIELD_NAMES = (
    'Count',
    'License',
)
DEFAULT_OUTPUT_FIELDS = (
    'Name',
    'Version',
)
SUMMARY_OUTPUT_FIELDS = (
    'Count',
    'License',
)

METADATA_KEYS = (
    'home-page',
    'author',
    'license',
    'summary',
    'license_classifier',
)
# Mapping of FIELD_NAMES to METADATA_KEYS where they differ by more than case
FIELDS_TO_METADATA_KEYS = {
    'URL': 'home-page',
    'Description': 'summary',
    'License-Metadata': 'license',
    'License-Classifier': 'license_classifier',
}
SYSTEM_PACKAGES = (
    __pkgname__,
    'pip',
    'PTable' if PTABLE else 'prettytable',
    'setuptools',
    'wheel',
)

LICENSE_UNKNOWN = 'UNKNOWN'


class NoValueEnum(Enum):
    def __repr__(self):  # pragma: no cover
        return '<%s.%s>' % (self.__class__.__name__, self.name)


class FromArg(NoValueEnum):
    META = M = auto()
    CLASSIFIER = C = auto()
    MIXED = MIX = auto()
    ALL = auto()


class OrderArg(NoValueEnum):
    COUNT = C = auto()
    LICENSE = L = auto()
    NAME = N = auto()
    AUTHOR = A = auto()
    URL = U = auto()


class FormatArg(NoValueEnum):
    PLAIN = P = auto()
    PLAIN_VERTICAL = auto()
    MARKDOWN = MD = M = auto()
    RST = REST = R = auto()
    CONFLUENCE = C = auto()
    HTML = H = auto()
    JSON = J = auto()
    JSON_LICENSE_FINDER = JLF = auto()
    CSV = auto()


class CustomNamespace(Namespace):
    from_: FromArg
    order: OrderArg
    format_: FormatArg
    summary: bool
    output_file: str
    ignore_packages: List[str]
    with_system: bool
    with_authors: bool
    with_urls: bool
    with_description: bool
    with_license_file: bool
    no_license_path: bool
    with_notice_file: bool
    filter_strings: bool
    filter_code_page: str
    fail_on: Optional[str]
    allow_only: Optional[str]


MAP_DEST_TO_ENUM = {
    'from_': FromArg,
    'order': OrderArg,
    'format_': FormatArg,
}
