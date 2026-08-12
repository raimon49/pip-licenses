# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et

# pip-licenses.cli.config
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


"""pip-licenses.cli.config

To be documented.
"""


from . import (
    __pkgname__,  # noqa: F401 -- Re-export as part of data API
    __version__,  # noqa: F401 -- Re-export as part of data API
    argparse,
)
from .pseudoChoices import (
    FormatArg,
    FromArg,
    OrderArg,
)


class Configuration(argparse.Namespace):
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
    with_license_files: bool  # added in v6.0
    no_license_path: bool
    with_notice_file: bool
    with_notice_files: bool  # added in v6.0
    with_other_files: bool  # added in v6.0
    filter_strings: bool
    filter_code_page: str
    partial_match: bool
    fail_on: str = None
    allow_only: str = None


CustomNamespace = Configuration
"""DEPRECIATED in v6.0; use piplicenses.cli.config.Configuration instead."""


__all__ = [
    """Configuration""",
    """CustomNamespace""",  # DEPRECIATED in v6.0+
]
