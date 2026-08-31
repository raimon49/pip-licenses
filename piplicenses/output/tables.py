# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et

# pip-licenses.output.tables
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


"""
pip-licenses.output.tables

To be documented.
"""

from collections import Counter
from collections.abc import (
    Iterator,
    Sequence,
)
from typing import Union

from ..cli import (
    Configuration,
)
from ..cli.pseudo_choices import (
    FormatArg,
)
from ..core import (
    get_packages,
    select_license_by_source,
)
from ..sorting import (
    SetLike,
)
from . import (
    DEFAULT_OUTPUT_FIELDS,
    DYNAMIC_FIELD_NAMES,
    FIELDS_TO_METADATA_KEYS,
    LICENSE_UNKNOWN,
    SUMMARY_FIELD_NAMES,
    __pkgname__,  # noqa: F401 -- Re-export as part of data API
    __version__,  # noqa: F401 -- Re-export as part of data API
    cast,
)
from ._csv import CSVPrettyTable  # the class
from ._json import JsonPrettyTable  # the class
from ._license_finder_json import JsonLicenseFinderTable  # the class
from ._plain_vertical import PlainVerticalTable  # the class
from ._prettytable_bridge import (
    HRuleStyle,
    PrettyTable,
)


def factory_styled_table_with_args(
    args: Configuration,
    output_fields: Union[SetLike, Sequence[str]] = DEFAULT_OUTPUT_FIELDS,
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
    if hasattr(table, "break_on_hyphens") and table.border:
        table.break_on_hyphens = (
            False  # changed in v6.0+ -- to support PrettyTable 3.12-3.16
        )

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


def _handle_multiple_value_field(
    key: str, value: Iterator[str]
) -> Union[str, list[str]]:
    """Normalize a metadata field that may contain one or many values.

    This helper converts an iterator of field values into the most convenient
    representation based on the field name:

    - If the field name ends with ``"s"`` (case-insensitive), the values are
      treated as plural and returned as a list.
    - Otherwise, the first value is returned as a single string.
    - If a plural field has no values, ``["UNKNOWN"]`` is returned.
    - If a singular field has no values, ``LICENSE_UNKNOWN`` is returned.

    Args:
        key: The field name used to decide whether the field should be treated
            as singular or plural.
        value: An iterator of string values for the field.

    Returns:
        Either:
        - a list of strings for plural fields, or
        - a single string for singular fields.

    Examples:
        A plural field returns all values as a list:

        >>> _handle_multiple_value_field("authors", iter(["Alice", "Bob"]))
        ['Alice', 'Bob']

        A singular field returns the first value:

        >>> _handle_multiple_value_field("license", iter(["MIT", "BSD"]))
        'MIT'

        An empty plural field falls back to ``["UNKNOWN"]``:

        >>> _handle_multiple_value_field("authors", iter([]))
        ['UNKNOWN']

        An empty singular field falls back to ``LICENSE_UNKNOWN``:

        >>> _handle_multiple_value_field("license", iter([]))
        'UNKNOWN'
    """
    if key.lower().endswith("s"):
        if isinstance(value, (str, bytes)):
            return [value or LICENSE_UNKNOWN]
        else:
            return sorted(value) or [LICENSE_UNKNOWN]
    return cast(
        str,
        next(iter(value), LICENSE_UNKNOWN)
        if not isinstance(value, str)
        else value or LICENSE_UNKNOWN,
    )


# TODO: change to accept set-like
def create_licenses_table(
    args: Configuration,
    output_fields: Union[set[str], Sequence[str]] = DEFAULT_OUTPUT_FIELDS,
) -> PrettyTable:
    table = factory_styled_table_with_args(args, output_fields)

    for pkg in get_packages(args):
        row: list[Union[str, list[str]]] = []
        for field in output_fields:
            if field == "License":
                license_set = select_license_by_source(
                    args.from_,
                    cast(list[str], pkg["license_classifier"]),
                    cast(str, pkg["license_metadata"]),
                    cast(str, pkg["license_expression"]),
                )
                _sorted_license_set = (
                    sorted(license_set) if license_set else []
                )
                _normalized_license_set = {
                    normal_item
                    for normal_item in _sorted_license_set
                    if normal_item is not None
                }
                license_str = "; ".join(_normalized_license_set)
                row.append(license_str)
            elif field == "License-Classifier":
                row.append(
                    "; ".join(sorted(pkg["license_classifier"]))
                    or LICENSE_UNKNOWN
                )
            elif field == "License-Expression":
                row.append(
                    cast(str, pkg["license_expression"]) or LICENSE_UNKNOWN
                )
            elif field == "License-Metadata":
                row.append(
                    cast(str, pkg["license_metadata"]) or LICENSE_UNKNOWN
                )
            elif (field.lower() in pkg) or (hasattr(pkg, field.lower())):
                row.append(cast(str, pkg[field.lower()]))
            else:
                if (field in FIELDS_TO_METADATA_KEYS) and (
                    FIELDS_TO_METADATA_KEYS[field] in pkg
                ):
                    value = pkg[FIELDS_TO_METADATA_KEYS[field]]
                    if value:
                        if field in DYNAMIC_FIELD_NAMES:
                            _value_as_list = cast(
                                list[str],
                                _handle_multiple_value_field(
                                    key=field,
                                    value=cast(Iterator[str], [*value]),
                                ),
                            )
                            if args.format_ in (
                                FormatArg.JSON,
                                FormatArg.PLAIN_VERTICAL,
                            ):  # Prototype
                                row.append(
                                    _value_as_list,
                                )
                            else:
                                if not isinstance(value, str):
                                    row.append(", ".join(_value_as_list))
                                else:
                                    row.append(cast(str, value))
                        else:
                            row.append(cast(str, value))
                    else:  # invalid value (e.g. None)
                        row.append(LICENSE_UNKNOWN)
                else:  # Unknown value (e.g. custom/future fields)
                    row.append(LICENSE_UNKNOWN)

        table.add_row(row)

    return table


def create_summary_table(args: Configuration) -> PrettyTable:
    counts = Counter(
        "; ".join(
            sorted(
                select_license_by_source(
                    args.from_,
                    cast(list[str], pkg["license_classifier"]),
                    cast(str, pkg["license_metadata"]),
                    cast(str, pkg["license_expression"]),
                )
            )
        )
        for pkg in get_packages(args)
    )

    table = factory_styled_table_with_args(args, SUMMARY_FIELD_NAMES)
    for license, count in counts.items():
        table.add_row([count, license])
    return table


__all__ = [
    """create_licenses_table""",
    """create_summary_table""",
    """factory_styled_table_with_args""",
]
