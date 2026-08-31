#!/usr/bin/env python
# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et

# pip-licenses.output
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


"""pip-licenses.output

To be documented.
"""

import hashlib
from functools import partial
from typing import (
    Union,
    cast,  # noqa: F401 -- (used by piplicenses.output._csv)
)

from .. import (
    DEFAULT_OUTPUT_FIELDS,
    DYNAMIC_FIELD_NAMES,  # noqa: F401 -- (used by piplicenses.output.tables)
    FIELDS_TO_METADATA_KEYS,  # noqa: F401 -- (used by piplicenses.output.tables)
    LICENSE_UNKNOWN,  # noqa: F401 -- (used by piplicenses.output.tables)
    SUMMARY_FIELD_NAMES,  # noqa: F401 -- (used by piplicenses.output.tables)
    SUMMARY_OUTPUT_FIELDS,
    __pkgname__,  # noqa: F401 -- Re-export as part of data API
    __version__,  # noqa: F401 -- Re-export as part of data API
)

#    because we are limited in python3.9 still by https://docs.python.org/3.9/library/stdtypes.html#dict
#    we create a simple value type for now:
strs = Union[str, list[str]]
#    dict_for_rows = dict[str, strs]
# or perhaps just PEP-589 (TypedDict)


from ..cli import (
    Configuration,
    FormatArg,  # used by create_output_string
    FromArg,  # used by get_output_fields
    get_sortby,
)
from ..sorting import (
    SetLike,  # noqa: F401 -- Re-export as part of our internal typing API
)

# See https://docs.python.org/3/reference/simple_stmts.html#the-import-statement
from ._csv import CSVPrettyTable

# See https://docs.python.org/3/reference/simple_stmts.html#the-import-statement
# Must import JsonPrettyTable before JsonLicenseFinderTable
from ._json import JsonPrettyTable

# See https://docs.python.org/3/reference/simple_stmts.html#the-import-statement
# Must import JsonLicenseFinderTable after JsonPrettyTable
from ._license_finder_json import JsonLicenseFinderTable

# placeholder for
# from ._prettytable_bridge import (
#    HRuleStyle,
#    PrettyTable,
#    RowType,
# )
# See https://docs.python.org/3/reference/simple_stmts.html#the-import-statement
from ._plain_vertical import PlainVerticalTable
from .consoles import (
    output_colored,
    save_if_needs,
)
from .tables import (
    create_licenses_table,
    create_summary_table,
    factory_styled_table_with_args,
)


def get_output_fields(args: Configuration) -> list[str]:
    if args.summary:
        return list(SUMMARY_OUTPUT_FIELDS)

    output_fields = list(DEFAULT_OUTPUT_FIELDS)

    if args.from_ == FromArg.ALL:
        output_fields.append("License-Metadata")
        output_fields.append("License-Classifier")
        output_fields.append("License-Expression")
        args.with_license_files = True  # overwrite
    else:
        # TODO: handle combos for JSON, and plain vertical
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
    # see PEP-387
    # see https://docs.python.org/3/library/exceptions.html#PendingDeprecationWarning
    # e.g., if not ("6.1" in __version__ and "6" in __version__ and "6.0" not in __version__):
    if args.with_license_files and args.format_ not in [
        FormatArg.JSON,
        FormatArg.PLAIN_VERTICAL,
    ]:
        if args.format_ not in (
            FormatArg.CONFLUENCE,
            FormatArg.HTML,
            FormatArg.MARKDOWN,
            FormatArg.PLAIN,
            FormatArg.RST,
        ):
            args.with_license_files = False  # unsupported combo
        # these are only supported in JSON and plain vertical
        args.with_notice_file = False
        args.with_notice_files = False
        args.with_other_files = False

    if args.no_file_paths:
        args.no_license_path = True

    _format_supports_file_text_data = False
    if args.format_ in (
        FormatArg.JSON,
        FormatArg.PLAIN,  # still a bit unwieldy
        FormatArg.PLAIN_VERTICAL,
        FormatArg.HTML,
    ):
        _format_supports_file_text_data = True

    if args.with_license_file or args.with_license_files:
        if not args.no_license_path:
            output_fields.append(
                "LicenseFiles" if args.with_license_files else "LicenseFile"
            )
        if _format_supports_file_text_data:
            output_fields.append(
                "LicenseTexts" if args.with_license_files else "LicenseText"
            )

        if args.with_notice_file or args.with_notice_files:
            if not args.no_file_paths:
                output_fields.append(
                    "NoticeFiles" if args.with_notice_files else "NoticeFile"
                )
            if _format_supports_file_text_data:
                output_fields.append("NoticeText")

        if args.with_other_files:
            if not args.no_file_paths:
                output_fields.append("OtherFiles")
            if _format_supports_file_text_data:
                output_fields.append("OtherText")

    return output_fields


def _create_stable_table_id(table_as_string: str) -> str:
    """Normalized SHA-256 hash based ID for the table with the given table string"""
    _seed = b""
    if table_as_string:
        # this is rather expensive but should ensure a stable result
        _seed = table_as_string.encode(
            encoding="utf-8", errors="backslashreplace"
        )
    _hashed_table = hashlib.sha3_256(_seed, usedforsecurity=False)
    _composed_id: str = f"pipl_tbl_{_hashed_table.hexdigest()}"
    return _composed_id


def create_output_string(args: Configuration) -> str:
    output_fields = get_output_fields(args)

    if args.summary:
        table = create_summary_table(args)
    else:
        table = create_licenses_table(args, output_fields)

    sortby = get_sortby(args)

    if args.format_ == FormatArg.HTML:
        _tbl_id = _create_stable_table_id(
            table.get_string(fields=output_fields, sortby=sortby)
        )
        html = table.get_html_string(
            fields=output_fields,
            sortby=sortby,
            attributes={"id": _tbl_id, "class": "pip_licenses_table"},
        )
        return html.encode("ascii", errors="xmlcharrefreplace").decode("ascii")
    else:
        return table.get_string(fields=output_fields, sortby=sortby)


def create_warn_string(args: Configuration) -> str:
    from ..cli import FormatArg  # workaround

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


# re-export for backwards compatibility and a stable API
__all__ = [
    """CSVPrettyTable""",
    """JsonLicenseFinderTable""",
    """JsonPrettyTable""",
    """PlainVerticalTable""",
    """create_licenses_table""",
    """create_output_string""",
    """create_summary_table""",
    """create_warn_string""",
    """factory_styled_table_with_args""",
    """get_output_fields""",
    """output_colored""",
    """save_if_needs""",
    """tables""",
]
