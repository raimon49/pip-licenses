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


from typing import Union

from prettytable import PrettyTable

from .. import (
    __pkgname__,  # noqa: F401 -- Re-export as part of data API
    __version__,  # noqa: F401 -- Re-export as part of data API
)

# Breaking change: version 6 will transition to support PEP-305 csv instead of pretty table (as csv is built-in)
from . import (
    cast,
    strs,
)

encodeable = Union[bytes, str]


COMMA: str = ","
"""Just the comma in CSV."""


class CSVPrettyTable(PrettyTable):
    """PrettyTable-like class exporting to CSV"""

    def get_string(self, **kwargs: strs) -> str:
        def _esc_quotes(val: encodeable) -> str:
            """
            Meta-escaping double quotes
            https://tools.ietf.org/html/rfc4180
            """
            try:
                return cast(str, val).replace('"', '""')
            except UnicodeDecodeError:  # pragma: no cover
                return cast(bytes, val).decode("utf-8").replace('"', '""')
            except UnicodeEncodeError:  # pragma: no cover
                return str(
                    cast(str, val).encode("unicode_escape").replace('"', '""')  # type: ignore[arg-type]
                )

        options = self._get_options(kwargs)
        rows = self._get_rows(options)
        formatted_rows = self._format_rows(rows)

        lines: list[str] = []
        formatted_header = COMMA.join(
            [f'"{_esc_quotes(val)}"' for val in self._field_names]
        )
        lines.append(formatted_header)
        lines.extend(
            [
                COMMA.join([f'"{_esc_quotes(val)}"' for val in row])
                for row in formatted_rows
            ]
        )

        return "\n".join(lines)


__all__ = [
    """COMMA""",
    """CSVPrettyTable""",
]
