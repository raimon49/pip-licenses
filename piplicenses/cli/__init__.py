#!/usr/bin/env python
# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et

# pip-licenses.cli
#
# MIT License
#
# Copyright (c) 2018-2025 raimon
# Copyright (c) 2025-2026 Mr. Walls
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


"""pip-licenses.cli

To be documented.
"""

import argparse
import codecs
import sys
from collections.abc import Sequence
from enum import Enum  # used by helper _expand_help
from importlib import (
    metadata as importlib_metadata,  # noqa: F401 -- (used by piplicenses.core)
)
from pathlib import Path

# See https://docs.python.org/3.14/library/argparse.html#color
from .. import (
    LEGACY_TOKEN,  # noqa: F401 -- (used by piplicenses.cli.config)
    Union,
    __pkgname__,
    __summary__,
    __version__,
    cast,
)
from .config import (
    DEFAULT_PYTHON,
    Configuration,
    CustomNamespace,  # noqa: F401 -- to be deprecated in v6
)

# if TYPE_CHECKING:
#    from typing import (
# watch for PEP-3124
#        overload,
#        Union,
#    )
#    NullableInt = Union[int, None]


# TODO: this is used elsewhere
# perhaps, this should go in sorting?
def get_sortby(args: Configuration) -> str:
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


# See https://docs.python.org/3.15/library/argparse.html#color
DEFAULT_USE_COLOR: Union[bool, None] = (
    True if sys.version_info >= (3, 14) else None
)


class CustomHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter
):  # pragma: no cover
    def __init__(
        self,
        prog: str,
        indent_increment: int = 2,
        max_help_position: int = 24,
        width: Union[int, None] = None,
        color: Union[bool, None] = DEFAULT_USE_COLOR,
    ) -> None:
        max_help_position = 30  # Minor Regression BUG from backport
        kwargs = {
            "indent_increment": indent_increment,
            "max_help_position": max_help_position,
            "width": width,
        }
        if DEFAULT_USE_COLOR is not None:
            if color is not None:
                kwargs["color"] = color
        else:
            kwargs.pop("color", None)
        super().__init__(prog, **kwargs)  # type: ignore[arg-type]

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
        args: Union[Sequence[str], None] = None,
        namespace: Union[argparse.Namespace, None] = None,
    ) -> Configuration:
        ns = super().parse_args(
            args=args if args and len(args) > 0 else [],
            namespace=namespace or None,
        )
        cfg = Configuration(**vars(ns))  # convert Namespace -> dataclass
        self._verify_args(cfg)
        return cfg

    def _verify_args(self, args: Configuration) -> None:
        if (
            args.with_license_file is False
            and args.with_license_files is False
        ) and (
            args.no_license_path is True
            or (
                (
                    args.with_notice_file is True
                    or args.with_notice_files is True
                )
                or args.with_other_files is True
            )
        ):
            self.error(
                "'--no-license-path' and '--with-notice-file[s]' "
                "as well as '--with-other-files' require "
                "the '--with-license-file[s]' option to be set"
            )
        if args.partial_match is True and (
            (args.fail_on is None or len(args.fail_on) <= 0)
            and (args.allow_on is None or len(args.allow_on) <= 0)
            and (
                (
                    "6.1" in __version__
                    and (args.warn_on is None or len(args.allow_on) <= 0)
                )
                or True
            )
        ):
            self.error(
                "'--partial-match' and '--simple-match' "
                "require at least one of "
                "the '--fail-on'/'--allow-only' options to be set."
                # An empty string will also not count.
            )
            # TODO: GHI-274 refactor for allow-package (name WIP)
            # e.g., "as well as '--allow-package' require "
            # TODO: GHI-274 refactor for warn-on
            # e.g., ".../'--warn-on' options ..."

        if args.filter_strings is False and args.filter_code_page != "latin1":
            self.error(
                "'--filter-code-page' requires the '--filter-strings' "
                "option to be set"
            )
        try:
            codecs.lookup(args.filter_code_page)  # type: ignore[arg-type]
        except LookupError:
            self.error(
                f"invalid code page '{args.filter_code_page}' given "
                "for '--filter-code-page, check "
                "https://docs.python.org/3/library/codecs.html#standard-encodings "
                "for valid code pages"
            )


from .pseudo_choices import (
    FormatArg,
    FromArg,
    NoValueEnum,
    OrderArg,
    choices_from_enum,
    enum_key_to_value,
    get_value_from_enum,
    value_to_enum_key,  # noqa: F401 -- Re-export as part of data API
)


class SelectAction(argparse.Action):
    # See https://github.com/astral-sh/ruff/issues/5243
    MAP_DEST_TO_ENUM: dict[str, type[NoValueEnum]] = {  # noqa: RUF100,RUF012
        "from_": FromArg,
        "order": OrderArg,
        "format_": FormatArg,
    }

    def __call__(  # type: ignore[override]
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str,
        option_string: Union[str, None] = None,
    ) -> None:
        enum_cls = type(self).MAP_DEST_TO_ENUM[self.dest]
        setattr(namespace, self.dest, get_value_from_enum(enum_cls, values))


from ..tomli_bridge import (
    tomllib,  # type: ignore[import-not-found]  # ty: ignore[unused-type-ignore-comment]
)


# TODO: this probably goes in utils (and SHOULD NOT BE vulnerable to 'open' MOCKING)
def load_config_from_file(pyproject_path: str) -> dict:
    if Path(pyproject_path).exists():
        with open(pyproject_path, "rb") as f:
            return tomllib.load(f).get("tool", {}).get(__pkgname__, {})
        # always has implicit f.close() from 'with' so no need to re-close
    return {}  # universal fallback to simple empty load


def _add_scope_arguments_to_parser(
    parser: CompatibleArgumentParser,
    include_system_pkg_default: bool,
    from_default: str,
    default_python: str,
    ignore_by_default: list,
    include_by_default: list,
) -> CompatibleArgumentParser:
    """Internal helper function.

    Not part of any public API. Do not rely on this function outside of this defining module.
    """
    if parser is not None:
        scope_group = parser.add_argument_group(
            "Scope",
            "Options to fine-tune source of packages {__pkgname__} will consider.",
        )
        system_toggle = scope_group.add_mutually_exclusive_group()
        system_toggle.add_argument(
            "-s",
            "--include-system",
            action="store_true",
            dest="include_from_system",
            default=include_system_pkg_default is True,
            help="dump with system packages",
        )
        system_toggle.add_argument(
            "--ignore-system",
            action="store_false",
            dest="include_from_system",
            help="R|Omit trivial system packages.\n"
            "e.g., 'include-system=False'.",
            default=include_system_pkg_default,
        )
        system_toggle.add_argument(
            "--with-system",
            action="store_true",
            dest="include_from_system",
            default=include_system_pkg_default is True,
            help="DEPRECATED; use --include-system instead.",
        )
        scope_group.add_argument(
            "--from",
            dest="from_",
            action=SelectAction,
            type=str,
            default=get_value_from_enum(FromArg, from_default),
            metavar="SOURCE",
            choices=choices_from_enum(FromArg),
            help="R|where to find license information\n"
            '"meta", "classifier", "expression", "mixed", "all"\n',
        )
        scope_group.add_argument(
            "--python",
            type=str,
            default=default_python,
            metavar="PYTHON_EXEC",
            help="R|path to python executable to search distributions from\n"
            "Package will be searched in the selected python's sys.path\n"
            "By default, will search packages for current env executable\n",
        )
        scope_group.add_argument(
            "-i",
            "--ignore-packages",
            action="extend",
            dest="ignore_packages",
            nargs="+",
            metavar="PKG",
            default=ignore_by_default,
            help="R|ignore selected package names and omit from output.\n"
            "May be used multiple times.",
        )
        scope_group.add_argument(
            "-p",
            "--packages",
            action="extend",
            dest="packages",
            nargs="+",
            metavar="PKG",
            default=include_by_default,
            help="R|only include selected packages in output.\n"
            "May be used multiple times.",
        )
    return parser


def _migrate_with_system_helper(config_from_file: dict) -> bool:
    """Use --include-system instead.

    Helper for migration in version v6.0.0
    """
    import warnings

    _conf_stub: bool = config_from_file.get(
        "with-system",  # DEPRECATED in v6.0+
        False,
    )
    if _conf_stub is True:
        warnings.warn(
            "DEPRECIATED in v6.0; use include-system instead."
            "This will be an error in the future."
            "See https://github.com/raimon49/pip-licenses/issues/349",
            stacklevel=2,
        )
    return _conf_stub


def _migrate_no_version_helper(config_from_file: dict) -> bool:
    """Use --without-version instead.

    Helper for migration in version v6.0.0
    """
    import warnings

    _conf_stub: bool = config_from_file.get(
        "no-version",  # DEPRECATED in v6.0+
        False,
    )
    if _conf_stub is True:
        warnings.warn(
            "DEPRECIATED in v6.0; use without-version instead."
            "This will be an error in the future."
            "See https://github.com/raimon49/pip-licenses/issues/349",
            stacklevel=2,
        )
    return _conf_stub


def _migrate_no_license_path_helper(config_from_file: dict) -> bool:
    """Use --without-license-paths instead.

    Helper for migration in version v6.0.0
    """
    import warnings

    _conf_stub: bool = config_from_file.get(
        "no-license-path",  # DEPRECATED in v6.0+
        False,
    )
    if _conf_stub is True:
        warnings.warn(
            "DEPRECIATED in v6.0; use include-system instead."
            "This will be an error in the future."
            "See https://github.com/raimon49/pip-licenses/issues/349",
            stacklevel=2,
        )
    return _conf_stub


def _add_verification_arguments_to_parser(
    parser: CompatibleArgumentParser,
    partial_match_default: bool,
    warn_by_default: list,  # unused atm
    allow_by_default: list,  # unused atm
    fail_by_default: Union[
        str, None
    ],  # will change to support lists in future
    require_by_default: Union[
        str, None
    ],  # will change to support lists in future
) -> CompatibleArgumentParser:
    """Internal helper function.

    Not part of any public API. Do not rely on this function outside of this defining module.
    """
    if parser is not None:
        verify_group = parser.add_argument_group(
            "Verification",
            "Options to verify licensing state of packages.",
            # after GHI-274 WILL CHANGE to "Options to stipulate licensing policy for packages.",
        )
        # placeholder for warn-on
        if "6.1" in __version__:
            verify_group.add_argument(
                "-W",
                "--warn-on",
                action="extend",
                dest="warn_on",
                nargs="+",
                metavar="WARN_ON",
                default=warn_by_default,
                help="R|warn (emitted to stderr) on the each occurrence\n"
                "of the specified licenses, but do not fail. Useful for\n"
                "licenses that have complex conditions (e.g., attribution,\n"
                "user notices, etc.). May be used multiple times.",
            )
            verify_group.add_argument(
                "--allow-packages",
                action="extend",
                dest="allow_packages",
                nargs="+",
                metavar="SAFE_PKG",
                default=warn_by_default,
                help="R|mark selected package(s) as explicitly permitted.\n"
                "Essentially ignores the selected packages when matching.\n"
                "May be used multiple times.",
            )
        verify_group.add_argument(
            "--fail-on",
            action="store",
            type=str,
            default=fail_by_default,
            help="R|fail (exit with code 1) on the first occurrence\n"
            "of the licenses of the semicolon-separated list",
        )
        verify_group.add_argument(
            "--allow-only",
            action="store",
            type=str,
            default=require_by_default,
            help="R|fail (exit with code 1) on the first occurrence\n"
            "of the licenses not in the semicolon-separated list",
        )
        partial_toggle = verify_group.add_mutually_exclusive_group()
        partial_toggle.add_argument(
            "--partial-match",
            action="store_true",
            dest="partial_match",
            default=partial_match_default is True,
            help="I|enables partial matching for --allow-only/--fail-on",
        )
        partial_toggle.add_argument(
            "--simple-match",  # added in v6.0+
            action="store_false",
            dest="partial_match",
            default=partial_match_default is True,
            help="I|avoids partial matching for --allow-only/--fail-on",
        )
    return parser


def _add_format_arguments_to_parser(
    parser: CompatibleArgumentParser,
    format_default: str,
    with_authors_default: bool,
    with_maintainers_default: bool,
    with_urls_default: bool,
    with_descriptions_default: bool,
    with_version_default: bool,
    filter_string_default: bool,
    filter_code_default: str,
) -> CompatibleArgumentParser:
    """Internal helper function.

    Not part of any public API. Do not rely on this function outside of this defining module.
    """
    if parser is not None:
        format_group = parser.add_argument_group(
            "Formatting",
            "Options to customize the output format.",
        )
        format_group.add_argument(
            "-f",
            "--format",
            dest="format_",
            action=SelectAction,
            type=str,
            default=get_value_from_enum(
                FormatArg,
                format_default,
            ),
            metavar="STYLE",
            choices=choices_from_enum(FormatArg),
            help="R|dump as set format style\n"
            '"plain", "plain-vertical" "markdown", "rst", \n'
            '"confluence", "html", "json", \n'
            '"json-license-finder",  "csv"\n',
        )

        format_toggle_authors = format_group.add_mutually_exclusive_group()
        format_toggle_authors.add_argument(
            "-a",
            "--with-authors",
            action="store_true",
            dest="with_authors",
            default=with_authors_default,
            help="dump with package authors",
        )
        format_toggle_authors.add_argument(
            "--without-authors",
            action="store_false",
            dest="with_authors",
            default=with_authors_default,
            help="dump with package authors",
        )
        format_toggle_maintainers = format_group.add_mutually_exclusive_group()
        format_toggle_maintainers.add_argument(
            "--with-maintainers",
            action="store_true",
            dest="with_maintainers",
            default=with_maintainers_default,
            help="dump with package maintainers",
        )
        format_toggle_maintainers.add_argument(
            "--without-maintainers",
            action="store_false",
            dest="with_maintainers",
            default=with_maintainers_default,
            help="omit package maintainers.",
        )
        format_toggle_urls = format_group.add_mutually_exclusive_group()
        format_toggle_urls.add_argument(
            "-u",
            "--with-urls",
            action="store_true",
            dest="with_urls",
            default=with_urls_default,
            help="dump with package urls",
        )
        format_toggle_urls.add_argument(
            "--without-urls",
            action="store_false",
            dest="with_urls",
            default=with_urls_default,
            help="dump with package urls",
        )
        format_toggle_description = format_group.add_mutually_exclusive_group()
        format_toggle_description.add_argument(
            "-d",
            "--with-descriptions",
            action="store_true",
            dest="with_description"
            if "6.0." in __version__
            else "with_descriptions",
            default=with_descriptions_default,
            help="dump with short package description",
        )
        format_toggle_description.add_argument(
            "--with-description",
            action="store_true",
            dest="with_description"
            if "6.0." in __version__
            else "with_descriptions",
            default=with_descriptions_default,
            help="See --with-descriptions"
            "DEPRECATED; use --with-descriptions instead.",
        )
        format_toggle_description.add_argument(
            "--without-descriptions",
            action="store_false",
            dest="with_description"
            if "6.0." in __version__
            else "with_descriptions",
            default=with_descriptions_default,
            help="Omits package descriptions. Inverse of --with-descriptions.",
        )
        format_toggle_version = format_group.add_mutually_exclusive_group()
        format_toggle_version.add_argument(
            "--without-version",
            action="store_true",
            dest="without_version",
            default=with_version_default,
            help="dump without package version.",
        )
        format_toggle_version.add_argument(
            "--with-version",
            action="store_false",
            dest="without_version",
            default=with_version_default,
            help="dump without package version.",
        )
        format_toggle_version.add_argument(
            "-nv",
            action="store_true",
            dest="without_version",
            default=with_version_default,
            help="DEPRECATED (for backwards compatibility); "
            "prefer --without-version instead.",
        )
        format_toggle_version.add_argument(
            "--no-version",
            action="store_true",
            dest="without_version",
            default=with_version_default,
            help="dump without package version. "
            "DEPRECATED; use --without-version.",
        )
        format_group.add_argument(
            "--filter-strings",
            action="store_true",
            default=filter_string_default,
            help="filter input according to code page.",
        )
        format_group.add_argument(
            "--filter-code-page",
            action="store",
            type=str,
            default=filter_code_default,
            metavar="CODE",
            help="I|specify code page for filtering.",
        )
    return parser


def create_parser(
    pyproject_path: str = "pyproject.toml",
) -> CompatibleArgumentParser:
    parser = CompatibleArgumentParser(
        prog=__pkgname__,  # added in v6.0+ -- to normalize usage and help
        description=__summary__,
        formatter_class=CustomHelpFormatter,
        conflict_handler="resolve",  # added in v6.0+
    )

    config_from_file = load_config_from_file(pyproject_path)
    parser = _add_scope_arguments_to_parser(
        parser=parser,
        include_system_pkg_default=config_from_file.get(
            "include-system",
            _migrate_with_system_helper(config_from_file),
        ),
        from_default=config_from_file.get("from", "mixed"),
        default_python=config_from_file.get("python", DEFAULT_PYTHON),
        ignore_by_default=config_from_file.get("ignore-packages", []),
        include_by_default=config_from_file.get("packages", []),
    )
    parser = _add_verification_arguments_to_parser(
        parser=parser,
        partial_match_default=config_from_file.get("partial-match", False),
        warn_by_default=config_from_file.get(
            "warn-on", []
        ),  # GH-274 currently unused
        allow_by_default=config_from_file.get(
            "allow-packages", []
        ),  # GH-274 currently unused
        fail_by_default=cast(
            Union[str, None], config_from_file.get("fail-on", None)
        ),
        require_by_default=cast(
            Union[str, None], config_from_file.get("allow-only", None)
        ),
    )
    mode_options = parser.add_argument_group(
        "Mode",
        "Options to select between modes. The default mode"
        "(no mode option), is to just dump the licenses",
    )
    license_file_options = parser.add_argument_group("License file options")
    # placeholder for format stuff
    _add_format_arguments_to_parser(
        parser=parser,
        format_default=config_from_file.get("format", "plain"),
        with_authors_default=config_from_file.get("with-authors", False),
        with_maintainers_default=config_from_file.get(
            "with-maintainers", False
        ),
        with_urls_default=config_from_file.get("with-urls", False),
        with_descriptions_default=config_from_file.get(
            "with-descriptions",
            config_from_file.get(
                "with-description", False
            ),  # kept for backwards compatibility
        ),
        with_version_default=config_from_file.get(
            "without-version",
            _migrate_no_version_helper(config_from_file),
        ),
        filter_string_default=config_from_file.get("filter-strings", False),
        filter_code_default=config_from_file.get("filter-code-page", "latin1"),
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{__pkgname__} {__version__}",
    )
    mode_options.add_argument(
        "--summary",
        action="store_true",
        default=config_from_file.get("summary", False),
        help="dump summary of each license",
    )
    mode_options.add_argument(
        "--output-file",
        action="store",
        type=lambda x: Path(x),
        default=config_from_file.get("output-file"),
        metavar="OUT",
        help=f"causes {__pkgname__}, to instead output to the specified file",
    )

    mode_options.add_argument(
        "-o",
        "--order",
        action=SelectAction,
        type=str,
        default=get_value_from_enum(
            OrderArg, config_from_file.get("order", "name")
        ),
        metavar="COL",
        choices=choices_from_enum(OrderArg),
        help='R|order by column\n"name", "license", "author", "url"\n',
    )

    license_file_options.add_argument(
        "-l",
        "--with-license-file",
        action="store_true",
        default=config_from_file.get("with-license-file", False),
        help="dump with location of license file and "
        "contents, most useful with JSON output. "
        "For structured formats (CSV, Markdown, reST), "
        "see README for workflow examples. "
        "DEPRECATED; use --with-license-files.",
    )
    license_file_options.add_argument(
        "--with-license-files",
        action="store_true",
        default=config_from_file.get("with-license-files", False),
        help="dump with location of each license file and contents, most useful with JSON output",
    )
    license_file_options.add_argument(
        "--without-license-paths",
        "--no-license-path",
        action="store_true",
        dest="no_license_path"
        if "6.0." in __version__
        else "without_license_paths",
        default=config_from_file.get(
            "without-license-paths",
            _migrate_no_license_path_helper(config_from_file),
        ),
        help="I|when specified together with option -l, "
        "suppress location of license file(s) in output",
    )
    license_file_options.add_argument(
        "--without-file-paths",
        "--no-file-paths",
        action="store_true",  # if "6.0." in __version__ else "store_false",
        dest="no_file_paths",  # if "6.0." in __version__ else "show-file-paths",
        default=config_from_file.get(
            "no-file-paths",  # if "6.0." in __version__ else "show-file-paths",
            False,  # if "6.0." in __version__ else True,
        ),
        help="I|Suppress location of file path(s) in output",
    )
    license_file_options.add_argument(
        "--with-notice-file",
        action="store_true",
        default=config_from_file.get("with-notice-file", False),
        help="I|when specified together with option -l, "
        "dump with location of up to one notice file and contents",
    )
    license_file_options.add_argument(
        "--with-notice-files",
        action="store_true",
        default=config_from_file.get("with-notice-files", False),
        help="I|when specified together with option -l, "
        "dump with location of all notice files and contents",
    )
    license_file_options.add_argument(
        "--without-notice-paths",  # added in v6.0+
        action="store_true",  # if "6.0." in __version__ else "store_const",
        dest="without_notice_paths",
        default=config_from_file.get("without-notice-paths", False),
        help="I|when specified together with option --with-notice-files, "
        "suppress location of notice file(s) in output",
    )
    license_file_options.add_argument(
        "--with-other-files",
        action="store_true",
        default=config_from_file.get("with-other-files", False),
        help="I|when specified together with option -l"
        " or --with-license-files, dump with location"
        " of other licensing-related files and contents",
    )
    license_file_options.add_argument(
        "--without-other-paths",  # added in v6.0+
        action="store_true",  # if "6.0." in __version__ else "store_const",
        dest="without_other_paths",
        default=config_from_file.get("without-other-paths", False),
        help="I|when specified together with option --with-other-files or --with-notice-files, "
        "suppress location of other file(s) in output",
    )

    return parser
