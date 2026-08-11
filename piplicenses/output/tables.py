#!/usr/bin/env python
# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et
"""
pip-licenses.output.tables

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


from . import (
    __pkgname__,  # noqa: F401 -- Re-export as part of data API
    __version__,  # noqa: F401 -- Re-export as part of data API
    annotations,  # noqa: F401 -- from piplicenses.__future__ -> piplicenses.output
    DEFAULT_OUTPUT_FIELDS,
)
from ..sorting import (
    SetLike,
)
from ..cli import (
    CustomNamespace
)
from ..cli.pseudoChoices import (
    FormatArg,
)
from prettytable import (
    HRuleStyle,
    PrettyTable,
)
from .JsonPrettyTable import JsonPrettyTable  # the class
from .JsonLicenseFinderTable import JsonLicenseFinderTable  # the class
from .CSVPrettyTable import CSVPrettyTable  # the class
from .PlainVerticalTable import PlainVerticalTable  # the class


def factory_styled_table_with_args(
    args: CustomNamespace,
    output_fields: SetLike = DEFAULT_OUTPUT_FIELDS,
) -> PrettyTable:
    table = PrettyTable()
    table.field_names = output_fields  # type: ignore[assignment]
    table.align = "l"  # type: ignore[assignment]
    table.border = args.format_ in (
        FormatArg.MARKDOWN,
        FormatArg.RST,
        FormatArg.CONFLUENCE,
        FormatArg.JSON,
    )
    table.header = True

    if args.format_ == FormatArg.MARKDOWN:
        table.junction_char = "|"
        table.hrules = HRuleStyle.HEADER
    elif args.format_ == FormatArg.RST:
        table.junction_char = "+"
        table.hrules = HRuleStyle.ALL
    elif args.format_ == FormatArg.CONFLUENCE:
        table.junction_char = "|"
        table.hrules = HRuleStyle.NONE
    elif args.format_ == FormatArg.JSON:
        table = JsonPrettyTable(table.field_names)
    elif args.format_ == FormatArg.JSON_LICENSE_FINDER:
        table = JsonLicenseFinderTable(table.field_names)
    elif args.format_ == FormatArg.CSV:
        table = CSVPrettyTable(table.field_names)
    elif args.format_ == FormatArg.PLAIN_VERTICAL:
        table = PlainVerticalTable(table.field_names)

    return table


__all__ = [
    """factory_styled_table_with_args""",
]
