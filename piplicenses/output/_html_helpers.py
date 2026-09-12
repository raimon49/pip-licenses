"""
HTML helper utilities for rendering license file lists and boxed text.

Drop these into the project and import where needed:

from piplicenses_html_helpers import (
    escape_html, attrs_to_str, wrap_tag, wrap_pre, wrap_ul, generate_html_id,
    format_license_files_html
)

The main API for consumers is `format_license_files_html`.
"""

import re
from collections.abc import (
    Iterable,
    Mapping,
)
from html import escape

from . import (
    Union,
    __pkgname__,  # noqa: F401 -- Re-export as part of internal API
    __version__,  # noqa: F401 -- Re-export as part of internal API
)

_UL_LI_TAG: re.Pattern = re.compile(
    r"&lt;(/?)(ul|li)&gt;",
    re.IGNORECASE,
)
"""Pattern to match escaped 'ul' and 'li' tags."""


def escape_html(text: str) -> str:
    """Escape HTML special characters in text.

    Note: non-ascii characters are preserved; the caller may perform
    xmlcharrefreplace encoding at the top-level output stage if needed.
    """
    if text is None:
        return ""
    return escape(text).replace('"', "&quot;").replace("'", "&#39;")


def attrs_to_str(attrs: Union[Mapping[str, str], None]) -> str:
    """Convert an attribute mapping to a string suitable for tag opening.

    Example:
      attrs_to_str({"id":"foo", "class":"bar"}) -> ' id="foo" class="bar"'
    """
    if not attrs:
        return ""
    parts: list[str] = []
    for k, v in sorted(attrs.items()):
        # attribute names should be ASCII-safe; escape the value
        parts.append(f'{k}="{escape_html(str(v))}"')
    return " " + " ".join(parts)


def wrap_tag(
    tag: str,
    inner: str = "",
    attrs: Union[Mapping[str, str], None] = None,
    inline: bool = False,
) -> str:
    """Wrap inner content with an HTML tag and optional attributes.

    If inline is False, the function adds newlines to better format block content.
    """
    attr_str = attrs_to_str(attrs)
    if inline:
        return f"<{tag}{attr_str}>{inner}</{tag}>"
    # block style with indentation for readability
    return f"<{tag}{attr_str}>\n{inner}\n</{tag}>"


def wrap_pre(text: str, attrs: Union[Mapping[str, str], None] = None) -> str:
    """Wrap escaped text into a <pre> block to preserve formatting (line breaks)."""
    escaped = escape_html(text)
    return wrap_tag("pre", escaped, attrs=attrs, inline=False)


def wrap_ul(
    items: Iterable[str],
    attrs: Union[Mapping[str, str], None] = None,
    li_attrs: Union[Mapping[str, str], None] = None,
) -> str:
    """Wrap an iterable of already-escaped/fully-formed HTML list-item bodies into a <ul>.

    Each item in `items` is expected to be a string content for <li> (not including <li> tags).
    This function will wrap each into <li>...</li> and return the <ul>...</ul> string.
    """
    # li_attr_str = attrs_to_str(li_attrs)
    lines = [wrap_tag("li", it, attrs=li_attrs, inline=True) for it in items]
    inner = "\n".join(lines)  # avoid <br> here to allow multi column formats
    return f"<ul{attrs_to_str(attrs)}>\n{inner}\n</ul>"


_ID_RE = re.compile(r"[^a-zA-Z0-9\-_]")


def generate_html_id(base: str, suffix: Union[str, None] = None) -> str:
    """Generate a safe HTML id attribute from base and optional suffix.

    Replaces unsafe characters with dashes and collapses multiple dashes.
    """
    if base is None:
        base = "id"
    combined = base if suffix is None else f"{base}-{suffix}"
    # replace characters not allowed (keep alnum, -, _)
    id_val = _ID_RE.sub("-", combined)
    # collapse multiple dashes and trim
    id_val = re.sub(r"-{2,}", "-", id_val).strip("-")
    if not id_val:
        return "id"
    return id_val


def replace_ul_li_tag(match: re.Match) -> str:
    return f"<{match.group(1)}{match.group(2)}>"


def unescape_ul_li(text: str) -> str:
    """Unescape only <ul>, </ul>, <li>, and </li> tags."""
    return _UL_LI_TAG.sub(replace_ul_li_tag, text)


# re-export for backwards compatibility and a stable API
__all__ = [
    # """format_license_files_html""",  # added in v6.0.0b11 and removed in v6.0.0b12
    """escape_html""",  # caution - not part of public api
    """generate_html_id""",
    """replace_ul_li_tag""",
    """unescape_ul_li""",
    """wrap_pre""",
    """wrap_tag""",
    """wrap_ul""",
]
