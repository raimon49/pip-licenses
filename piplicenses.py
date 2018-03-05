#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et
"""
pip-licenses

MIT License

Copyright (c) 2018 raimon

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from __future__ import (division, print_function,
                        absolute_import, unicode_literals)
import sys
import argparse
from email.parser import FeedParser
from email import message_from_string

import pip
from prettytable import PrettyTable
from prettytable.prettytable import HEADER as RULE_HEADER, ALL as RULE_ALL

__pkgname__ = 'pip-licenses'
__version__ = '1.6.1'
__author__ = 'raimon'
__license__ = 'MIT License'
__summary__ = ('Dump the software license list of '
               'Python packages installed with pip.')
__url__ = 'https://github.com/raimon49/pip-licenses'


FIELD_NAMES = (
    'Name',
    'Version',
    'License',
    'Author',
    'URL',
)


DEFAULT_OUTPUT_FIELDS = (
    'Name',
    'Version',
    'License',
)


METADATA_KEYS = (
    'home-page',
    'author',
    'license',
)


SYSTEM_PACKAGES = (
    __pkgname__,
    'pip',
    'PTable',
    'setuptools',
    'wheel',
)

LICENSE_UNKNOWN = 'UNKNOWN'


def create_licenses_table(args):
    def get_pkg_info(pkg):
        pkg_info = {
            'name': pkg.project_name,
            'version': pkg.version,
            'namever': str(pkg),
        }
        metadata = None
        if pkg.has_metadata('METADATA'):
            metadata = pkg.get_metadata('METADATA')

        if pkg.has_metadata('PKG-INFO') and metadata is None:
            metadata = pkg.get_metadata('PKG-INFO')

        if metadata is None:
            for key in METADATA_KEYS:
                pkg_info[key] = LICENSE_UNKNOWN

            return pkg_info

        feed_parser = FeedParser()
        feed_parser.feed(metadata)
        parsed_metadata = feed_parser.close()

        for key in METADATA_KEYS:
            pkg_info[key] = parsed_metadata.get(key, LICENSE_UNKNOWN)

        if args.from_classifier and metadata is not None:
            message = message_from_string(metadata)
            pkg_info['license'] = find_license_from_classifier(message)

        return pkg_info

    table = factory_styled_table_with_args(args)

    pkgs = pip.get_installed_distributions()
    ignore_pkgs_as_lower = [pkg.lower() for pkg in args.ignore_packages]
    for pkg in pkgs:
        pkg_info = get_pkg_info(pkg)
        pkg_name = pkg_info['name']

        if pkg_name.lower() in ignore_pkgs_as_lower:
            continue

        if not args.with_system and pkg_name in SYSTEM_PACKAGES:
            continue

        table.add_row([pkg_info['name'],
                       pkg_info['version'],
                       pkg_info['license'],
                       pkg_info['author'],
                       pkg_info['home-page'], ])

    return table


def factory_styled_table_with_args(args):
    table = PrettyTable()
    table.field_names = FIELD_NAMES
    table.align = 'l'
    table.border = (args.format_markdown or args.format_rst)
    table.header = True

    if args.format_markdown:
        table.junction_char = '|'
        table.hrules = RULE_HEADER
    elif args.format_rst:
        table.junction_char = '+'
        table.hrules = RULE_ALL

    return table


def find_license_from_classifier(message):
    license_from_classifier = LICENSE_UNKNOWN

    licenses = []
    for k, v in message.items():
        if k == 'Classifier' and v.startswith('License'):
            licenses.append(v.split(' :: ')[-1])

    if len(licenses) > 0:
        license_from_classifier = ', '.join(licenses)

    return license_from_classifier


def get_output_fields(args):
    output_fields = list(DEFAULT_OUTPUT_FIELDS)

    if args.with_authors:
        output_fields.append('Author')

    if args.with_urls:
        output_fields.append('URL')

    return output_fields


def get_sortby(args):
    if args.order == 'name':
        return 'Name'
    elif args.order == 'license':
        return 'License'
    elif args.order == 'author' and args.with_authors:
        return 'Author'
    elif args.order == 'url' and args.with_urls:
        return 'URL'

    return 'Name'


def create_output_string(args):
    table = create_licenses_table(args)
    output_fields = get_output_fields(args)
    sortby = get_sortby(args)

    if args.format_html:
        return table.get_html_string(fields=output_fields, sortby=sortby)
    else:
        return table.get_string(fields=output_fields, sortby=sortby)


def create_parser():
    parser = argparse.ArgumentParser(
        description=__summary__)
    parser.add_argument('-v', '--version',
                        action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('-c', '--from-classifier',
                        action='store_true',
                        default=False,
                        help='find license from classifier')
    parser.add_argument('-s', '--with-system',
                        action='store_true',
                        default=False,
                        help='dump with system packages')
    parser.add_argument('-a', '--with-authors',
                        action='store_true',
                        default=False,
                        help='dump with package authors')
    parser.add_argument('-u', '--with-urls',
                        action='store_true',
                        default=False,
                        help='dump with package urls')
    parser.add_argument('-i', '--ignore-packages',
                        action='store', type=str,
                        nargs='+', metavar='PKG',
                        default=[],
                        help='ignore package name in dumped list')
    parser.add_argument('-o', '--order',
                        action='store', type=str,
                        default='name', metavar='COL',
                        help=('order by column\n'
                              '"name", "license", "author", "url"\n'
                              'default: --order=name'))
    parser.add_argument('-m', '--format-markdown',
                        action='store_true',
                        default=False,
                        help='dump as markdown style')
    parser.add_argument('-r', '--format-rst',
                        action='store_true',
                        default=False,
                        help='dump as reST style')
    parser.add_argument('--format-html',
                        action='store_true',
                        default=False,
                        help='dump as html style')

    return parser


def main():  # pragma: no cover
    parser = create_parser()
    args = parser.parse_args()

    output_string = create_output_string(args)
    print(output_string)


if __name__ == '__main__':  # pragma: no cover
    main()
