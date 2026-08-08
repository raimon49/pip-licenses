#!/usr/bin/env python
# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et
"""
pip-licenses

MIT License

Copyright (c) 2018-2025 raimon
Copyright (c) 2025-2026 Mr. Walls

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

from .. import (
    __pkgname__,
    __version__,
    __summary__,
    annotations,
    TYPE_CHECKING,
)

import argparse
import codecs
import sys

import os
import re
import subprocess

from collections import Counter
from collections.abc import Callable, Generator, Iterable, Iterator, Sequence
from functools import partial
from importlib import metadata as importlib_metadata
from importlib.metadata import Distribution
from pathlib import Path

from .config import (
    CustomNamespace,  # to be deprecated in v6
)


if TYPE_CHECKING:
    from typing import (
        cast,
#        Union,
    )
#    NullableInt = Union[int, None]

# TODO: this is used elsewhere
def get_sortby(args: CustomNamespace) -> str:
    if args.summary and args.order == OrderArg.COUNT:
        return "Count"
    elif args.summary or args.order == OrderArg.LICENSE:
        return "License"
    elif args.order == OrderArg.NAME:
        return "Name"
    elif args.order == OrderArg.AUTHOR and args.with_authors:
        return "Author"
    elif args.order == OrderArg.MAINTAINER and args.with_maintainers:
        return "Maintainer"
    elif args.order == OrderArg.URL and args.with_urls:
        return "URL"

    return "Name"


def create_warn_string(args: CustomNamespace) -> str:
    warn_messages = []
    warn = partial(output_colored, "33")

    if args.with_license_file and args.format_ != FormatArg.JSON:
        message = warn(
            "Due to the length of these fields, this option is "
            "best paired with --format=json."
        )
        warn_messages.append(message)

    if args.summary and (args.with_authors or args.with_urls):
        message = warn(
            "When using this option, only --order=count or "
            "--order=license has an effect for the --order "
            "option. And using --with-authors and --with-urls "
            "will be ignored."
        )
        warn_messages.append(message)

    return "\n".join(warn_messages)


class CustomHelpFormatter(argparse.HelpFormatter):  # pragma: no cover
    def __init__(
        self,
        prog: str,
        indent_increment: int = 2,
        max_help_position: int = 24,
        width: int = None,
    ) -> None:
        max_help_position = 30
        super().__init__(
            prog,
            indent_increment=indent_increment,
            max_help_position=max_help_position,
            width=width,
        )

    def _format_action(self, action: argparse.Action) -> str:
        flag_indent_argument: bool = False
        text = self._expand_help(action)
        separator_pos = text[:3].find("|")
        if separator_pos != -1 and "I" in text[:separator_pos]:
            self._indent()
            flag_indent_argument = True
        help_str = super()._format_action(action)
        if flag_indent_argument:
            self._dedent()
        return help_str

    def _expand_help(self, action: argparse.Action) -> str:
        if isinstance(action.default, Enum):
            default_value = enum_key_to_value(action.default)
            return cast(str, self._get_help_string(action)) % {
                "default": default_value
            }
        return super()._expand_help(action)

    def _split_lines(self, text: str, width: int) -> list[str]:
        separator_pos = text[:3].find("|")
        if separator_pos != -1:
            flag_splitlines: bool = "R" in text[:separator_pos]
            text = text[separator_pos + 1:]  # fmt: skip
            if flag_splitlines:
                return text.splitlines()
        return super()._split_lines(text, width)


class CompatibleArgumentParser(argparse.ArgumentParser):
    def parse_args(  # type: ignore[override]
        self,
        args: Sequence[str] = None,
        namespace: CustomNamespace = None,
    ) -> CustomNamespace:
        args_ = cast(CustomNamespace, super().parse_args(args, namespace))
        self._verify_args(args_)
        return args_

    def _verify_args(self, args: CustomNamespace) -> None:
        if args.with_license_file is False and (
            args.no_license_path is True or args.with_notice_file is True
        ):
            self.error(
                "'--no-license-path' and '--with-notice-file' require "
                "the '--with-license-file' option to be set"
            )
        if args.filter_strings is False and args.filter_code_page != "latin1":
            self.error(
                "'--filter-code-page' requires the '--filter-strings' "
                "option to be set"
            )
        try:
            codecs.lookup(args.filter_code_page)
        except LookupError:
            self.error(
                f"invalid code page '{args.filter_code_page}' given "
                "for '--filter-code-page, check "
                "https://docs.python.org/3/library/codecs.html#standard-encodings "
                "for valid code pages"
            )


from .pseudoChoices import (
    NoValueEnum,
    FromArg,
    OrderArg,
    FormatArg,
    value_to_enum_key,
    enum_key_to_value,
    choices_from_enum,
    get_value_from_enum,
)


class SelectAction(argparse.Action):

    MAP_DEST_TO_ENUM: dict[str, type[NoValueEnum]] = {
        "from_": FromArg,
        "order": OrderArg,
        "format_": FormatArg,
    }

    def __call__(  # type: ignore[override]
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str,
        option_string: str = None,
    ) -> None:
        enum_cls = MAP_DEST_TO_ENUM[self.dest]
        setattr(namespace, self.dest, get_value_from_enum(enum_cls, values))


from ..tomli_bridge import tomllib  # type: ignore[import-not-found]  # ty: ignore[unused-type-ignore-comment]

# TODO: this probably goes in utils (and SHOULD NOT BE vulnerable to 'open' MOCKING)
def load_config_from_file(pyproject_path: str) -> dict:
    if Path(pyproject_path).exists():
        with open(pyproject_path, "rb") as f:
            return tomllib.load(f).get("tool", {}).get(__pkgname__, {})
        # always has implicit f.close() from 'with' so no need to re-close
    return {}  # universal fallback to simple empty load


def create_parser(
    pyproject_path: str = "pyproject.toml",
) -> CompatibleArgumentParser:
    parser = CompatibleArgumentParser(
        description=__summary__, formatter_class=CustomHelpFormatter
    )

    config_from_file = load_config_from_file(pyproject_path)

    common_options = parser.add_argument_group("Common options")
    format_options = parser.add_argument_group("Format options")
    verify_options = parser.add_argument_group("Verify options")

    lit_prog_pat = "%(prog)s"
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{lit_prog_pat} {__version__}",
    )

    common_options.add_argument(
        "--python",
        type=str,
        default=config_from_file.get("python", sys.executable),
        metavar="PYTHON_EXEC",
        help="R| path to python executable to search distributions from\n"
        "Package will be searched in the selected python's sys.path\n"
        "By default, will search packages for current env executable\n"
        "(default: sys.executable)",
    )

    common_options.add_argument(
        "--from",
        dest="from_",
        action=SelectAction,
        type=str,
        default=get_value_from_enum(
            FromArg, config_from_file.get("from", "mixed")
        ),
        metavar="SOURCE",
        choices=choices_from_enum(FromArg),
        help="R|where to find license information\n"
        '"meta", "classifier, "mixed", "all"\n'
        "(default: %(default)s)",
    )
    common_options.add_argument(
        "-o",
        "--order",
        action=SelectAction,
        type=str,
        default=get_value_from_enum(
            OrderArg, config_from_file.get("order", "name")
        ),
        metavar="COL",
        choices=choices_from_enum(OrderArg),
        help="R|order by column\n"
        '"name", "license", "author", "url"\n'
        "(default: %(default)s)",
    )
    common_options.add_argument(
        "-f",
        "--format",
        dest="format_",
        action=SelectAction,
        type=str,
        default=get_value_from_enum(
            FormatArg, config_from_file.get("format", "plain")
        ),
        metavar="STYLE",
        choices=choices_from_enum(FormatArg),
        help="R|dump as set format style\n"
        '"plain", "plain-vertical" "markdown", "rst", \n'
        '"confluence", "html", "json", \n'
        '"json-license-finder",  "csv"\n'
        "(default: %(default)s)",
    )
    common_options.add_argument(
        "--summary",
        action="store_true",
        default=config_from_file.get("summary", False),
        help="dump summary of each license",
    )
    common_options.add_argument(
        "--output-file",
        action="store",
        default=config_from_file.get("output-file"),
        type=str,
        help="save license list to file",
    )
    common_options.add_argument(
        "-i",
        "--ignore-packages",
        action="store",
        type=str,
        nargs="+",
        metavar="PKG",
        default=config_from_file.get("ignore-packages", []),
        help="ignore package name in dumped list",
    )
    common_options.add_argument(
        "-p",
        "--packages",
        action="store",
        type=str,
        nargs="+",
        metavar="PKG",
        default=config_from_file.get("packages", []),
        help="only include selected packages in output",
    )
    format_options.add_argument(
        "-s",
        "--with-system",
        action="store_true",
        default=config_from_file.get("with-system", False),
        help="dump with system packages",
    )
    format_options.add_argument(
        "-a",
        "--with-authors",
        action="store_true",
        default=config_from_file.get("with-authors", False),
        help="dump with package authors",
    )
    format_options.add_argument(
        "--with-maintainers",
        action="store_true",
        default=config_from_file.get("with-maintainers", False),
        help="dump with package maintainers",
    )
    format_options.add_argument(
        "-u",
        "--with-urls",
        action="store_true",
        default=config_from_file.get("with-urls", False),
        help="dump with package urls",
    )
    format_options.add_argument(
        "-d",
        "--with-description",
        action="store_true",
        default=config_from_file.get("with-description", False),
        help="dump with short package description",
    )
    format_options.add_argument(
        "-nv",
        "--no-version",
        action="store_true",
        default=config_from_file.get("no-version", False),
        help="dump without package version",
    )
    format_options.add_argument(
        "-l",
        "--with-license-file",
        action="store_true",
        default=config_from_file.get("with-license-file", False),
        help="dump with location of license file and "
        "contents, most useful with JSON output. "
        "For structured formats (CSV, Markdown, reST), "
        "see README for workflow examples.",
    )
    format_options.add_argument(
        "--no-license-path",
        action="store_true",
        default=config_from_file.get("no-license-path", False),
        help="I|when specified together with option -l, "
        "suppress location of license file output",
    )
    format_options.add_argument(
        "--with-notice-file",
        action="store_true",
        default=config_from_file.get("with-notice-file", False),
        help="I|when specified together with option -l, "
        "dump with location of license file and contents",
    )
    format_options.add_argument(
        "--filter-strings",
        action="store_true",
        default=config_from_file.get("filter-strings", False),
        help="filter input according to code page",
    )
    format_options.add_argument(
        "--filter-code-page",
        action="store",
        type=str,
        default=config_from_file.get("filter-code-page", "latin1"),
        metavar="CODE",
        help="I|specify code page for filtering (default: %(default)s)",
    )

    verify_options.add_argument(
        "--fail-on",
        action="store",
        type=str,
        default=config_from_file.get("fail-on", None),
        help="fail (exit with code 1) on the first occurrence "
        "of the licenses of the semicolon-separated list",
    )
    verify_options.add_argument(
        "--allow-only",
        action="store",
        type=str,
        default=config_from_file.get("allow-only", None),
        help="fail (exit with code 1) on the first occurrence "
        "of the licenses not in the semicolon-separated list",
    )
    verify_options.add_argument(
        "--partial-match",
        action="store_true",
        default=config_from_file.get("partial-match", False),
        help="enables partial matching for --allow-only/--fail-on",
    )

    return parser

# placeholder for compatibility shim, E.g.,
#if __name__ == "__main__":  # pragma: no cover
#    ..__main__.main()
