

from piplicenses import __pkgname__


if TYPE_CHECKING:  # pragma: no cover
    pass

# Mapping of FIELD_NAMES to METADATA_KEYS where they differ by more than case
FIELDS_TO_METADATA_KEYS = {
    "URL": "homepage",
    "License-Metadata": "license",
    "License-Classifier": "license_classifier",
    "LicenseFile": "license_files",
    "LicenseFiles": "license_files",
    "LicenseText": "license_texts",
    "LicenseTexts": "license_texts",
    "NoticeFile": "notice_files",
    "NoticeFiles": "notice_files",
    "NoticeText": "notice_texts",
    "NoticeTexts": "notice_texts",
    "OtherFiles": "other_files",
    "OtherTexts": "other_texts",
    "Description": "summary",
}

_MULTI_VALUE_KEYS = {
    "LicenseFile",
    "LicenseFiles",
    "LicenseText",
    "LicenseTexts",
    "NoticeFile",
    "NoticeFiles",
    "NoticeText",
    "NoticeTexts",
    "OtherFiles",
    "OtherTexts",
}


def _handle_multiple_value_field(key: str, value: Iterator[str]) -> str | list[str]:
    if key.endswith("s"):
        return list(value) or ["UNKNOWN"]
    return cast(str, next(value, LICENSE_UNKNOWN))

def create_licenses_table(
    args: CustomNamespace,
    output_fields: Sequence[str] = DEFAULT_OUTPUT_FIELDS,
) -> PrettyTable:
    table = factory_styled_table_with_args(args, output_fields)

    for pkg in get_packages(args):
        row: list[str | list[str]] = []
        for field in output_fields:
            if field == "License":
                license_set = pkg.license_names
                license_str = "; ".join(sorted(license_set))
                row.append(license_str)
            elif field == "License-Classifier":
                row.append("; ".join(sorted(pkg.license_classifiers)) or LICENSE_UNKNOWN)
            elif hasattr(pkg, field.lower()):
                row.append(cast(str, getattr(pkg, field.lower())))
            else:
                value = getattr(pkg, FIELDS_TO_METADATA_KEYS[field])
                if field in _MULTI_VALUE_KEYS:
                    row.append(_handle_multiple_value_field(field, value))
                else:
                    row.append(cast(str, value))
        table.add_row(row)

    return table




class PlainVerticalTable(PrettyTable):
    """PrettyTable for outputting to a simple non-column based style.

    When used with --with-license-file, this style is similar to the default
    style generated from Angular CLI's --extractLicenses flag.
    """

    def get_string(self, **kwargs: str | list[str]) -> str:
        options = self._get_options(kwargs)
        rows = self._get_rows(options)
        show_paths = "LicenseFiles" in kwargs["fields"]

        output = ""
        for row in rows:
            index = 0
            while index < len(row):
                v = row[index]
                if isinstance(v, list):
                    if show_paths:
                        for first_entry, second_entry in zip(v, row[index + 1]):
                            output += "{}\n{}\n".format(first_entry, second_entry)
                        index += 1
                    else:
                        for entry in v:
                            output += "{}\n".format(entry)
                else:
                    output += "{}\n".format(v)
                index += 1
            output += "\n"

        return output


class CustomNamespace(argparse.Namespace):
    from_: FromArg
    order: OrderArg
    format_: FormatArg
    summary: bool
    output_file: str
    ignore_packages: list[str]
    packages: list[str]
    with_system: bool
    with_authors: bool
    with_urls: bool
    with_description: bool
    with_license_file: bool
    with_license_files: bool
    no_license_path: bool
    with_notice_file: bool
    with_notice_files: bool
    with_other_files: bool
    filter_strings: bool
    filter_code_page: str
    partial_match: bool
    fail_on: str | None
    allow_only: str | None
    collect_all_failures: bool


def get_output_fields(args: CustomNamespace) -> list[str]:
    if args.summary:
        return list(SUMMARY_OUTPUT_FIELDS)

    output_fields = list(DEFAULT_OUTPUT_FIELDS)

    if args.from_ == FromArg.ALL:
        output_fields.append("License-Metadata")
        output_fields.append("License-Classifier")
    else:
        output_fields.append("License")

    if args.with_authors:
        output_fields.append("Author")

    if args.with_maintainers:
        output_fields.append("Maintainer")

    if args.with_urls:
        output_fields.append("URL")

    if args.with_description:
        output_fields.append("Description")

    if args.no_version:
        output_fields.remove("Version")

    if args.with_license_files and args.format_ not in [FormatArg.JSON, FormatArg.PLAIN_VERTICAL]:
        args.with_license_files = False
        args.with_notice_files = False
        args.with_other_files = False

    if args.with_license_file or args.with_license_files:
        if not args.no_license_path:
            output_fields.append("LicenseFiles" if args.with_license_files else "LicenseFile")

        output_fields.append("LicenseTexts" if args.with_license_files else "LicenseText")

        if args.with_notice_file or args.with_notice_files:
            if not args.no_license_path:
                output_fields.append("NoticeFiles" if args.with_notice_files else "NoticeFile")
            output_fields.append("NoticeTexts" if args.with_notice_files else "NoticeText")
        if args.with_other_files:
            if not args.no_license_path:
                output_fields.append("OtherFiles")
            output_fields.append("OtherTexts")

    return output_fields




class CompatibleArgumentParser(argparse.ArgumentParser):
    def parse_args(  # type: ignore[override]
        self,
        args: None | Sequence[str] = None,
        namespace: None | CustomNamespace = None,
    ) -> CustomNamespace:
        args_ = cast(CustomNamespace, super().parse_args(args, namespace))
        self._verify_args(args_)
        return args_

    def _verify_args(self, args: CustomNamespace) -> None:
        if args.with_license_file is False and args.with_license_files is False:
            if args.no_license_path is True or args.with_notice_file is True or args.with_notice_files is True or args.with_other_files is True:
                self.error(
                    "'--no-license-path' and '--with-notice-file[s]' as well as '--with-other-files' require the '--with-license-file[s]' option to be set"
                )
        if args.filter_strings is False and args.filter_code_page != "latin1":
            self.error("'--filter-code-page' requires the '--filter-strings' option to be set")
        try:
            codecs.lookup(args.filter_code_page)
        except LookupError:
            self.error(
                f"invalid code page {args.filter_code_page!r} given for '--filter-code-page, check "
                "https://docs.python.org/3/library/codecs.html#standard-encodings for valid code pages"
            )


class CustomNamespace(argparse.Namespace):
    from_: FromArg
    order: OrderArg
    format_: FormatArg
    summary: bool
    output_file: str
    ignore_packages: list[str]
    packages: list[str]
    with_system: bool
    with_authors: bool
    with_urls: bool
    with_description: bool
    with_license_file: bool
    with_license_files: bool
    no_license_path: bool
    with_notice_file: bool
    with_notice_files: bool
    with_other_files: bool
    filter_strings: bool
    filter_code_page: str
    partial_match: bool
    fail_on: str | None
    allow_only: str | None
    collect_all_failures: bool


def get_output_fields(args: CustomNamespace) -> list[str]:
    if args.summary:
        return list(SUMMARY_OUTPUT_FIELDS)

    output_fields = list(DEFAULT_OUTPUT_FIELDS)

    if args.from_ == FromArg.ALL:
        output_fields.append("License-Metadata")
        output_fields.append("License-Classifier")
    else:
        output_fields.append("License")

    if args.with_authors:
        output_fields.append("Author")

    if args.with_maintainers:
        output_fields.append("Maintainer")

    if args.with_urls:
        output_fields.append("URL")

    if args.with_description:
        output_fields.append("Description")

    if args.no_version:
        output_fields.remove("Version")

    if args.with_license_files and args.format_ not in [FormatArg.JSON, FormatArg.PLAIN_VERTICAL]:
        args.with_license_files = False
        args.with_notice_files = False
        args.with_other_files = False

    if args.with_license_file or args.with_license_files:
        if not args.no_license_path:
            output_fields.append("LicenseFiles" if args.with_license_files else "LicenseFile")

        output_fields.append("LicenseTexts" if args.with_license_files else "LicenseText")

        if args.with_notice_file or args.with_notice_files:
            if not args.no_license_path:
                output_fields.append("NoticeFiles" if args.with_notice_files else "NoticeFile")
            output_fields.append("NoticeTexts" if args.with_notice_files else "NoticeText")
        if args.with_other_files:
            if not args.no_license_path:
                output_fields.append("OtherFiles")
            output_fields.append("OtherTexts")

    return output_fields




class CompatibleArgumentParser(argparse.ArgumentParser):
    def parse_args(  # type: ignore[override]
        self,
        args: None | Sequence[str] = None,
        namespace: None | CustomNamespace = None,
    ) -> CustomNamespace:
        args_ = cast(CustomNamespace, super().parse_args(args, namespace))
        self._verify_args(args_)
        return args_

    def _verify_args(self, args: CustomNamespace) -> None:
        if args.with_license_file is False and args.with_license_files is False:
            if args.no_license_path is True or args.with_notice_file is True or args.with_notice_files is True or args.with_other_files is True:
                self.error(
                    "'--no-license-path' and '--with-notice-file[s]' as well as '--with-other-files' require the '--with-license-file[s]' option to be set"
                )
        if args.filter_strings is False and args.filter_code_page != "latin1":
            self.error("'--filter-code-page' requires the '--filter-strings' option to be set")
        try:
            codecs.lookup(args.filter_code_page)
        except LookupError:
            self.error(
                f"invalid code page {args.filter_code_page!r} given for '--filter-code-page, check "
                "https://docs.python.org/3/library/codecs.html#standard-encodings for valid code pages"
            )




def create_parser(
    pyproject_path: str = "pyproject.toml",
) -> CompatibleArgumentParser:
    parser = CompatibleArgumentParser(description=__summary__, formatter_class=CustomHelpFormatter)

    config_from_file = load_config_from_file(pyproject_path)

    common_options = parser.add_argument_group("Common options")
    format_options = parser.add_argument_group("Format options")
    verify_options = parser.add_argument_group("Verify options")

    parser.add_argument("-v", "--version", action="version", version="%(prog)s " + __version__)

    common_options.add_argument(
        "--python",
        type=str,
        default=config_from_file.get("python", sys.executable),
        metavar="PYTHON_EXEC",
        help=(
            "R| path to python executable to search distributions from\n"
            "Package will be searched in the selected python's sys.path\n"
            "By default, will search packages for current env executable\n"
            "(default: sys.executable)"
        ),
    )

    common_options.add_argument(
        "--from",
        dest="from_",
        action=SelectAction,
        type=str,
        default=get_value_from_enum(FromArg, config_from_file.get("from", "mixed")),
        metavar="SOURCE",
        choices=choices_from_enum(FromArg),
        help='R|where to find license information\n"meta", "classifier, "mixed", "all"\n(default: %(default)s)',
    )
    common_options.add_argument(
        "-o",
        "--order",
        action=SelectAction,
        type=str,
        default=get_value_from_enum(OrderArg, config_from_file.get("order", "name")),
        metavar="COL",
        choices=choices_from_enum(OrderArg),
        help='R|order by column\n"name", "license", "author", "url"\n(default: %(default)s)',
    )
    common_options.add_argument(
        "-f",
        "--format",
        dest="format_",
        action=SelectAction,
        type=str,
        default=get_value_from_enum(FormatArg, config_from_file.get("format", "plain")),
        metavar="STYLE",
        choices=choices_from_enum(FormatArg),
        help=(
            "R|dump as set format style\n"
            '"plain", "plain-vertical" "markdown", "rst", \n'
            '"confluence", "html", "json", \n'
            '"json-license-finder",  "csv"\n'
            "(default: %(default)s)"
        ),
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
        help="dump with location of license file and contents, most useful with JSON output",
    )
    format_options.add_argument(
        "--with-license-files",
        action="store_true",
        default=config_from_file.get("with-license-files", False),
        help="dump with location of license files and contents, most useful with JSON output",
    )
    format_options.add_argument(
        "--no-license-path",
        action="store_true",
        default=config_from_file.get("no-license-path", False),
        help="I|when specified together with option -l, suppress location of license file output",
    )
    format_options.add_argument(
        "--with-notice-file",
        action="store_true",
        default=config_from_file.get("with-notice-file", False),
        help="I|when specified together with option -l, dump with location of notice files and contents",
    )
    format_options.add_argument(
        "--with-notice-files",
        action="store_true",
        default=config_from_file.get("with-notice-files", False),
        help="I|when specified together with option -l or --with-license-files, dump with location of notice files and contents",
    )
    format_options.add_argument(
        "--with-other-files",
        action="store_true",
        default=config_from_file.get("with-other-files", False),
        help="I|when specified together with option -l or --with-license-files, dump with location of other licensing-related files and contents",
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
        help="fail (exit with code 1) on the first occurrence of the licenses of the semicolon-separated list",
    )
    verify_options.add_argument(
        "--allow-only",
        action="store",
        type=str,
        default=config_from_file.get("allow-only", None),
        help="fail (exit with code 1) on the first occurrence of the licenses not in the semicolon-separated list",
    )
    verify_options.add_argument(
        "--partial-match",
        action="store_true",
        default=config_from_file.get("partial-match", False),
        help="enables partial matching for --allow-only/--fail-on",
    )
    verify_options.add_argument(
        "--collect-all-failures",
        action="store_true",
        default=config_from_file.get("collect-all-failures", False),
        help="collect all license failures and report them after processing all packages",
    )

    return parser
