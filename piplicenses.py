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
import glob
import os
import codecs
import argparse
from functools import partial
from email.parser import FeedParser
from email import message_from_string

try:
    from pip._internal.utils.misc import get_installed_distributions
except ImportError:
    from pip import get_installed_distributions
from prettytable import PrettyTable
from prettytable.prettytable import (FRAME as RULE_FRAME, ALL as RULE_ALL,
                                     HEADER as RULE_HEADER, NONE as RULE_NONE)

__pkgname__ = 'pip-licenses'
__version__ = '1.16.1'
__author__ = 'raimon'
__license__ = 'MIT License'
__summary__ = ('Dump the software license list of '
               'Python packages installed with pip.')
__url__ = 'https://github.com/raimon49/pip-licenses'


FIELD_NAMES = (
    'Name',
    'Version',
    'License',
    'LicenseFile',
    'LicenseText',
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
    'License',
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
)

# Mapping of FIELD_NAMES to METADATA_KEYS where they differ by more than case
FIELDS_TO_METADATA_KEYS = {
    'URL': 'home-page',
    'Description': 'summary',
}


SYSTEM_PACKAGES = (
    __pkgname__,
    'pip',
    'PTable',
    'setuptools',
    'wheel',
)

LICENSE_UNKNOWN = 'UNKNOWN'


def get_packages(args):

    def get_pkg_license_file(pkg):
        """
        Attempt to find the package's LICENSE file on disk and return the
        tuple (license_file_path, license_file_contents).
        """
        license_file = LICENSE_UNKNOWN
        license_text = LICENSE_UNKNOWN
        pkg_dirname = "{}-{}.dist-info".format(
            pkg.project_name.replace("-", "_"), pkg.version)
        license_file_base = os.path.join(pkg.location, pkg_dirname, 'LICENSE*')
        for test_file in glob.glob(license_file_base):
            if os.path.exists(test_file):
                license_file = test_file
                with codecs.open(test_file,
                                 encoding='utf-8',
                                 errors='replace') as license_file_handle:
                    file_lines = license_file_handle.readlines()
                try:
                    # python 3 is happy with maybe-Unicode files
                    license_text = "".join(file_lines)
                except UnicodeDecodeError:  # pragma: no cover
                    # python 2 not so much
                    license_text = "".join([line.decode('utf-8', 'replace')
                                            for line in file_lines])
                break
        return (license_file, license_text)

    def get_pkg_info(pkg):
        (license_file, license_text) = get_pkg_license_file(pkg)
        pkg_info = {
            'name': pkg.project_name,
            'version': pkg.version,
            'namever': str(pkg),
            'licensefile': license_file,
            'licensetext': license_text,
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

        from_source = getattr(args, 'from')
        need_classifier = from_source == 'classifier' or from_source == 'mixed'
        if need_classifier and metadata is not None:
            message = message_from_string(metadata)
            license_classifier = find_license_from_classifier(message)
            license_meta = pkg_info['license']
            # Overwrite license by condition
            pkg_info['license'] = select_license_by_source(from_source,
                                                           license_classifier,
                                                           license_meta)

        return pkg_info

    pkgs = get_installed_distributions()
    ignore_pkgs_as_lower = [pkg.lower() for pkg in args.ignore_packages]
    for pkg in pkgs:
        pkg_name = pkg.project_name

        if pkg_name.lower() in ignore_pkgs_as_lower:
            continue

        if not args.with_system and pkg_name in SYSTEM_PACKAGES:
            continue

        pkg_info = get_pkg_info(pkg)
        yield pkg_info


def create_licenses_table(args, output_fields=DEFAULT_OUTPUT_FIELDS):
    table = factory_styled_table_with_args(args, output_fields)

    for pkg in get_packages(args):
        row = []
        for field in output_fields:
            if field.lower() in pkg:
                row.append(pkg[field.lower()])
            else:
                row.append(pkg[FIELDS_TO_METADATA_KEYS[field]])
        table.add_row(row)

    return table


def create_summary_table(args):
    licenses = {}
    for pkg in get_packages(args):
        if pkg['license'] not in licenses:
            licenses.update({pkg['license']: 1})
        else:
            licenses[pkg['license']] += 1

    table = factory_styled_table_with_args(args, SUMMARY_FIELD_NAMES)
    for license in licenses.keys():
        table.add_row([licenses[license],
                       license, ])
    return table


class JsonPrettyTable(PrettyTable):
    """PrettyTable-like class exporting to JSON"""

    def _format_row(self, row, options):
        resrow = {}
        for (field, value) in zip(self._field_names, row):
            if field not in options["fields"]:
                continue

            resrow[field] = value

        return resrow

    def get_string(self, **kwargs):
        # import included here in order to limit dependencies
        # if not interested in JSON output,
        # then the dependency is not required
        import json

        options = self._get_options(kwargs)
        rows = self._get_rows(options)
        formatted_rows = self._format_rows(rows, options)

        lines = []
        for row in formatted_rows:
            lines.append(row)

        return json.dumps(lines, indent=2, sort_keys=True)


class JsonLicenseFinderTable(JsonPrettyTable):
    def _format_row(self, row, options):
        resrow = {}
        for (field, value) in zip(self._field_names, row):
            if field == 'Name':
                resrow['name'] = value

            if field == 'Version':
                resrow['version'] = value

            if field == 'License':
                resrow['licenses'] = [value]

        return resrow

    def get_string(self, **kwargs):
        # import included here in order to limit dependencies
        # if not interested in JSON output,
        # then the dependency is not required
        import json

        options = self._get_options(kwargs)
        rows = self._get_rows(options)
        formatted_rows = self._format_rows(rows, options)

        lines = []
        for row in formatted_rows:
            lines.append(row)

        return json.dumps(lines, sort_keys=True)


class CSVPrettyTable(PrettyTable):
    """PrettyTable-like class exporting to CSV"""

    def get_string(self, **kwargs):

        def esc_quotes(val):
            """
            Meta-escaping double quotes
            https://tools.ietf.org/html/rfc4180
            """
            try:
                return val.replace('"', '""')
            except UnicodeDecodeError:  # pragma: no cover
                return val.decode('utf-8').replace('"', '""')
            except UnicodeEncodeError:  # pragma: no cover
                return val.encode('unicode_escape').replace('"', '""')

        options = self._get_options(kwargs)
        rows = self._get_rows(options)
        formatted_rows = self._format_rows(rows, options)

        lines = []
        formatted_header = ','.join(['"%s"' % (esc_quotes(val), )
                                     for val in self._field_names])
        lines.append(formatted_header)
        for row in formatted_rows:
            formatted_row = ','.join(['"%s"' % (esc_quotes(val), )
                                      for val in row])
            lines.append(formatted_row)

        return '\n'.join(lines)


def factory_styled_table_with_args(args, output_fields=DEFAULT_OUTPUT_FIELDS):
    table = PrettyTable()
    table.field_names = output_fields
    table.align = 'l'
    table.border = (args.format == 'markdown' or args.format == 'rst' or
                    args.format == 'confluence' or args.format == 'json')
    table.header = True

    if args.format == 'markdown':
        table.junction_char = '|'
        table.hrules = RULE_HEADER
    elif args.format == 'rst':
        table.junction_char = '+'
        table.hrules = RULE_ALL
    elif args.format == 'confluence':
        table.junction_char = '|'
        table.hrules = RULE_NONE
    elif args.format == 'json':
        table = JsonPrettyTable(table.field_names)
    elif args.format == 'json-license-finder':
        table = JsonLicenseFinderTable(table.field_names)
    elif args.format == 'csv':
        table = CSVPrettyTable(table.field_names)

    return table


def find_license_from_classifier(message):
    license_from_classifier = LICENSE_UNKNOWN

    licenses = []
    for k, v in message.items():
        if k == 'Classifier' and v.startswith('License'):
            license = v.split(' :: ')[-1]

            # Through the declaration of 'Classifier: License :: OSI Approved'
            if license != 'OSI Approved':
                licenses.append(license)

    if len(licenses) > 0:
        license_from_classifier = ', '.join(licenses)

    return license_from_classifier


def select_license_by_source(from_source, license_classifier, license_meta):
    if from_source == 'classifier':
        return license_classifier
    elif from_source == 'mixed':
        if license_classifier != LICENSE_UNKNOWN:
            return license_classifier
        else:
            return license_meta


def get_output_fields(args):
    if args.summary:
        return list(SUMMARY_OUTPUT_FIELDS)

    output_fields = list(DEFAULT_OUTPUT_FIELDS)

    if args.with_authors:
        output_fields.append('Author')

    if args.with_urls:
        output_fields.append('URL')

    if args.with_description:
        output_fields.append('Description')

    if args.with_license_file:
        output_fields.append('LicenseFile')
        output_fields.append('LicenseText')

    return output_fields


def get_sortby(args):
    if args.summary and args.order == 'count':
        return 'Count'
    elif args.summary or args.order == 'license':
        return 'License'
    elif args.order == 'name':
        return 'Name'
    elif args.order == 'author' and args.with_authors:
        return 'Author'
    elif args.order == 'url' and args.with_urls:
        return 'URL'

    return 'Name'


def create_output_string(args):
    output_fields = get_output_fields(args)

    if args.summary:
        table = create_summary_table(args)
    else:
        table = create_licenses_table(args, output_fields)

    sortby = get_sortby(args)

    if args.format == 'html':
        return table.get_html_string(fields=output_fields, sortby=sortby)
    else:
        return table.get_string(fields=output_fields, sortby=sortby)


def create_warn_string(args):
    warn_messages = []
    warn = partial(output_colored, '33')

    if args.with_license_file and not args.format == 'json':
        message = warn(('Due to the length of these fields, this option is '
                        'best paired with --format=json.'))
        warn_messages.append(message)

    if args.summary and (args.with_authors or args.with_urls):
        message = warn(('When using this option, only --order=count or '
                        '--order=license has an effect for the --order '
                        'option. And using --with-authors and --with-urls '
                        'will be ignored.'))
        warn_messages.append(message)

    if args.from_classifier:
        message = warn(('The option "--from-classifier" is deprecated. '
                        'Please migrate to "--from=classifier".'))
        warn_messages.append(message)

    if (args.format_markdown or args.format_rst or args.format_confluence or
            args.format_html or args.format_json):
        message = warn(('The option "--format-xxx" is deprecated. '
                        'Please migrate to "--format=xxx".'))
        warn_messages.append(message)

    return '\n'.join(warn_messages)


class CompatibleArgumentParser(argparse.ArgumentParser):

    def parse_args(self, args=None, namespace=None):
        args = super(CompatibleArgumentParser, self).parse_args(args,
                                                                namespace)
        self._compatible_format_args(args)

        return args

    def _compatible_format_args(self, args):
        from_input = getattr(args, 'from').lower()
        order_input = args.order.lower()
        format_input = args.format.lower()

        # XXX: Use enum when drop support Python 2.7
        if from_input in ('meta', 'm'):
            setattr(args, 'from', 'meta')

        if from_input in ('classifier', 'c'):
            setattr(args, 'from', 'classifier')

        if from_input in ('mixed', 'mix'):
            setattr(args, 'from', 'mixed')

        if order_input in ('count', 'c'):
            args.order = 'count'

        if order_input in ('license', 'l'):
            args.order = 'license'

        if order_input in ('name', 'n'):
            args.order = 'name'

        if order_input in ('author', 'a'):
            args.order = 'author'

        if order_input in ('url', 'u'):
            args.order = 'url'

        if format_input in ('plain', 'p'):
            args.format = 'plain'

        if format_input in ('markdown', 'md', 'm'):
            args.format = 'markdown'

        if format_input in ('rst', 'rest', 'r'):
            args.format = 'rst'

        if format_input in ('confluence', 'c'):
            args.format = 'confluence'

        if format_input in ('html', 'h'):
            args.format = 'html'

        if format_input in ('json', 'j'):
            args.format = 'json'

        if format_input in ('json-license-finder', 'jlf'):
            args.format = 'json-license-finder'

        if format_input in ('csv', ):
            args.format = 'csv'

        if args.from_classifier:
            setattr(args, 'from', 'classifier')

        if args.format_markdown:
            args.format = 'markdown'
        elif args.format_rst:
            args.format = 'rst'
        elif args.format_confluence:
            args.format = 'confluence'
        elif args.format_html:
            args.format = 'html'
        elif args.format_json:
            args.format = 'json'


def create_parser():
    parser = CompatibleArgumentParser(
        description=__summary__)
    parser.add_argument('-v', '--version',
                        action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('--from',
                        action='store', type=str,
                        default='meta', metavar='SOURCE',
                        help=('where to find license information\n'
                              '"meta", "classifier, "mixed"\n'
                              'default: --from=meta'))
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
    parser.add_argument('-d', '--with-description',
                        action='store_true',
                        default=False,
                        help='dump with short package description')
    parser.add_argument('-l', '--with-license-file',
                        action='store_true',
                        default=False,
                        help='dump with location of license file and '
                             'contents, most useful with JSON output')
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
    parser.add_argument('-f', '--format',
                        action='store', type=str,
                        default='plain', metavar='STYLE',
                        help=('dump as set format style\n'
                              '"plain", "markdown", "rst", "confluence",\n'
                              '"html", "json", "json-license-finder",  "csv"\n'
                              'default: --format=plain'))
    parser.add_argument('-m', '--format-markdown',
                        action='store_true',
                        default=False,
                        help='dump as markdown style')
    parser.add_argument('-r', '--format-rst',
                        action='store_true',
                        default=False,
                        help='dump as reST style')
    parser.add_argument('--format-confluence',
                        action='store_true',
                        default=False,
                        help='dump as confluence wiki style')
    parser.add_argument('--format-html',
                        action='store_true',
                        default=False,
                        help='dump as html style')
    parser.add_argument('--format-json',
                        action='store_true',
                        default=False,
                        help='dump as json')
    parser.add_argument('--summary',
                        action='store_true',
                        default=False,
                        help='dump summary of each license')

    return parser


def output_colored(code, text, is_bold=False):
    """
    Create function to output with color sequence
    """
    if is_bold:
        code = '1;%s' % code

    return '\033[%sm%s\033[0m' % (code, text)


def main():  # pragma: no cover
    parser = create_parser()
    args = parser.parse_args()

    output_string = create_output_string(args)
    print(output_string)
    warn_string = create_warn_string(args)
    if warn_string:
        print(warn_string, file=sys.stderr)


if __name__ == '__main__':  # pragma: no cover
    main()
