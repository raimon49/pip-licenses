#!/usr/bin/env python
# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et
"""
pip-licenses.output

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
    annotations,
    TYPE_CHECKING,
    SUMMARY_OUTPUT_FIELDS,
    DEFAULT_OUTPUT_FIELDS,
)

# placeholder for strs
from typing import (
    cast,
    Union,
)
#    because we are limmited in python3.9 still by https://docs.python.org/3.9/library/stdtypes.html#dict
#    we create a simple value type for now:
strs = Union[str, list[str]]
#    dict_for_rows = dict[str, strs]
# or perhaps just PEP-589 (TypedDict)


from .consoles import (
    save_if_needs,
    output_colored,
)

from ..cli import (
    CustomNamespace,
)

from ..sorting import (
    SetLike,
)

from prettytable import (
    HRuleStyle,
    PrettyTable,
    RowType,
)


from .JsonPrettyTable import JsonPrettyTable
from .JsonLicenseFinderTable import JsonLicenseFinderTable
from .CSVPrettyTable import CSVPrettyTable


from .PlainVerticalTable import PlainVerticalTable

from .tables import factory_styled_table_with_args


def get_output_fields(args: CustomNamespace) -> list[str]:
    if args.summary:
        return list(SUMMARY_OUTPUT_FIELDS)

    output_fields = list(DEFAULT_OUTPUT_FIELDS)

    if args.from_ == FromArg.ALL:
        output_fields.append("License-Metadata")
        output_fields.append("License-Classifier")
        output_fields.append("License-Expression")
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

    if args.with_license_file:
        if not args.no_license_path:
            output_fields.append("LicenseFile")

        output_fields.append("LicenseText")

        if args.with_notice_file:
            output_fields.append("NoticeText")
            if not args.no_license_path:
                output_fields.append("NoticeFile")

    return output_fields

# placeholder for consoles (from split-cli)
def create_output_string(args: CustomNamespace) -> str:
    output_fields = get_output_fields(args)

    if args.summary:
        table = create_summary_table(args)
    else:
        table = create_licenses_table(args, output_fields)

    sortby = get_sortby(args)

    if args.format_ == FormatArg.HTML:
        html = table.get_html_string(fields=output_fields, sortby=sortby)
        return html.encode("ascii", errors="xmlcharrefreplace").decode("ascii")
    else:
        return table.get_string(fields=output_fields, sortby=sortby)


# re-export for backwards compatibility and a stable API
__all__ = [
    """JsonPrettyTable""",
    """JsonLicenseFinderTable""",
    """CSVPrettyTable""",
    """PlainVerticalTable""",
    """factory_styled_table_with_args""",
    """tables""",
    """get_output_fields""",
    """create_output_string""",
    """save_if_needs""",
    """output_colored""",
]
