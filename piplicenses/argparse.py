# ---------------------------------------------------------------------------
# Licensed under the MIT License. See LICENSE file for license information.
# ---------------------------------------------------------------------------
import codecs
from argparse import Action, ArgumentParser, HelpFormatter, Namespace
from enum import Enum
from typing import List, Optional, Sequence, Text

from .const import (
    MAP_DEST_TO_ENUM, CustomNamespace, FormatArg, FromArg, OrderArg,
    __summary__, __version__)
from .utils import (
    choices_from_enum, enum_key_to_value, value_to_enum_key)


class CustomHelpFormatter(HelpFormatter):  # pragma: no cover
    def __init__(
        self, prog: Text, indent_increment: int = 2,
        max_help_position: int = 24, width: Optional[int] = None
    ) -> None:
        max_help_position = 30
        super().__init__(
            prog, indent_increment=indent_increment,
            max_help_position=max_help_position, width=width)

    def _format_action(self, action: Action) -> str:
        flag_indent_argument: bool = False
        text = self._expand_help(action)
        separator_pos = text[:3].find('|')
        if separator_pos != -1 and 'I' in text[:separator_pos]:
            self._indent()
            flag_indent_argument = True
        help_str = super()._format_action(action)
        if flag_indent_argument:
            self._dedent()
        return help_str

    def _expand_help(self, action: Action) -> str:
        if isinstance(action.default, Enum):
            default_value = enum_key_to_value(action.default)
            return self._get_help_string(action) % {'default': default_value}
        return super()._expand_help(action)

    def _split_lines(self, text: Text, width: int) -> List[str]:
        separator_pos = text[:3].find('|')
        if separator_pos != -1:
            flag_splitlines: bool = 'R' in text[:separator_pos]
            text = text[separator_pos + 1:]
            if flag_splitlines:
                return text.splitlines()
        return super()._split_lines(text, width)


class SelectAction(Action):
    def __call__(
        self, parser: ArgumentParser,
        namespace: Namespace,
        values: Text,
        option_string: Optional[Text] = None,
    ) -> None:
        enum_cls = MAP_DEST_TO_ENUM[self.dest]
        values = value_to_enum_key(values)
        setattr(namespace, self.dest, getattr(enum_cls, values))


class CompatibleArgumentParser(ArgumentParser):
    def parse_args(self, args: Optional[Sequence[Text]] = None,
                   namespace: CustomNamespace = None) -> CustomNamespace:
        args = super().parse_args(args, namespace)
        self._verify_args(args)
        return args

    def _verify_args(self, args: CustomNamespace):
        if args.with_license_file is False and (
                args.no_license_path is True or
                args.with_notice_file is True):
            self.error(
                "'--no-license-path' and '--with-notice-file' require "
                "the '--with-license-file' option to be set")
        if args.filter_strings is False and \
                args.filter_code_page != 'latin1':
            self.error(
                "'--filter-code-page' requires the '--filter-strings' "
                "option to be set")
        try:
            codecs.lookup(args.filter_code_page)
        except LookupError:
            self.error(
                "invalid code page '%s' given for '--filter-code-page, "
                "check https://docs.python.org/3/library/codecs.html"
                "#standard-encodings for valid code pages"
                % args.filter_code_page)


def create_parser():
    parser = CompatibleArgumentParser(
        description=__summary__,
        formatter_class=CustomHelpFormatter)

    common_options = parser.add_argument_group('Common options')
    format_options = parser.add_argument_group('Format options')
    verify_options = parser.add_argument_group('Verify options')

    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s ' + __version__)

    common_options.add_argument(
        '--from',
        dest='from_',
        action=SelectAction, type=str,
        default=FromArg.MIXED, metavar='SOURCE',
        choices=choices_from_enum(FromArg),
        help='R|where to find license information\n'
             '"meta", "classifier, "mixed", "all"\n'
             '(default: %(default)s)')
    common_options.add_argument(
        '-o', '--order',
        action=SelectAction, type=str,
        default=OrderArg.NAME, metavar='COL',
        choices=choices_from_enum(OrderArg),
        help='R|order by column\n'
             '"name", "license", "author", "url"\n'
             '(default: %(default)s)')
    common_options.add_argument(
        '-f', '--format',
        dest='format_',
        action=SelectAction, type=str,
        default=FormatArg.PLAIN, metavar='STYLE',
        choices=choices_from_enum(FormatArg),
        help='R|dump as set format style\n'
             '"plain", "plain-vertical" "markdown", "rst", \n'
             '"confluence", "html", "json", \n'
             '"json-license-finder",  "csv"\n'
             '(default: %(default)s)')
    common_options.add_argument(
        '--summary',
        action='store_true',
        default=False,
        help='dump summary of each license')
    common_options.add_argument(
        '--output-file',
        action='store', type=str,
        help='save license list to file')
    common_options.add_argument(
        '-i', '--ignore-packages',
        action='store', type=str,
        nargs='+', metavar='PKG',
        default=[],
        help='ignore package name in dumped list')

    format_options.add_argument(
        '-s', '--with-system',
        action='store_true',
        default=False,
        help='dump with system packages')
    format_options.add_argument(
        '-a', '--with-authors',
        action='store_true',
        default=False,
        help='dump with package authors')
    format_options.add_argument(
        '-u', '--with-urls',
        action='store_true',
        default=False,
        help='dump with package urls')
    format_options.add_argument(
        '-d', '--with-description',
        action='store_true',
        default=False,
        help='dump with short package description')
    format_options.add_argument(
        '-l', '--with-license-file',
        action='store_true',
        default=False,
        help='dump with location of license file and '
             'contents, most useful with JSON output')
    format_options.add_argument(
        '--no-license-path',
        action='store_true',
        default=False,
        help='I|when specified together with option -l, '
             'suppress location of license file output')
    format_options.add_argument(
        '--with-notice-file',
        action='store_true',
        default=False,
        help='I|when specified together with option -l, '
             'dump with location of license file and contents')
    format_options.add_argument(
        '--filter-strings',
        action="store_true",
        default=False,
        help='filter input according to code page')
    format_options.add_argument(
        '--filter-code-page',
        action="store", type=str,
        default="latin1",
        metavar="CODE",
        help='I|specify code page for filtering '
             '(default: %(default)s)')

    verify_options.add_argument(
        '--fail-on',
        action='store', type=str,
        default=None,
        help='fail (exit with code 1) on the first occurrence '
             'of the licenses of the semicolon-separated list')
    verify_options.add_argument(
        '--allow-only',
        action='store', type=str,
        default=None,
        help='fail (exit with code 1) on the first occurrence '
             'of the licenses not in the semicolon-separated list')

    return parser
