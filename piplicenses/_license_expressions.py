# vim:fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et
#
# pip-licenses._license_expressions
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


"""Small, dependency-free parser for the structure of SPDX expressions.

This intentionally does not consult the SPDX license or exception registry. It
recognizes the expression grammar needed by ``--allow-only`` and returns the
license operands (excluding WITH exceptions). Invalid or partially parsed input
returns ``None`` so callers can retain their legacy whole-string behavior.
"""

from typing import (
    # See https://github.com/raimon49/pip-licenses/issues/360
    Literal,  # after python 3.11 see LiteralString too
    Union,
)

from . import (
    DOCUMENT_LICENSE_EXPRESSION_REF_PATTERN,
    INDIRECT_LICENSE_EXPRESSION_REF_PATTERN,
    LICENSE_EXPRESSION_IDENTIFIER_PATTERN,
    LICENSE_EXPRESSION_TOKEN_PATTERN,
    __pkgname__,  # noqa: F401 -- Re-export as part of data API
    __version__,  # noqa: F401 -- Re-export as part of data API
)

_OR: Literal["OR"] = "OR"
"""Hardcoded 'OR' keyword.

See [GHI-360](https://github.com/raimon49/pip-licenses/issues/360).

Literally:

    >>> _OR == "OR"
    True
    >>>

"""


_AND: Literal["AND"] = "AND"
"""Hardcoded 'AND' keyword.

See [GHI-360](https://github.com/raimon49/pip-licenses/issues/360).

Literally:

    >>> _AND == "AND"
    True
    >>>

"""


_WITH: Literal["WITH"] = "WITH"
"""Hardcoded 'WITH' keyword.

See [GHI-360](https://github.com/raimon49/pip-licenses/issues/360).

Literally:

    >>> _WITH == "WITH"
    True
    >>>

"""


# Rationale for these literals:
# No joke, but bandit thinks these might be hardcoded passwords...
# so we make it explicit hardcoded here instead of a confusing  # nosec


_OPN_TOK: Literal["("] = "("
"""Hardcoded '(' group token.

See [GHI-360](https://github.com/raimon49/pip-licenses/issues/360).

Literally:

    >>> _OPN_TOK is "("
    True
    >>>

"""


_CLS_TOK: Literal[")"] = ")"
"""Hardcoded ')' group token.

See [GHI-360](https://github.com/raimon49/pip-licenses/issues/360).

Literally:

    >>> _CLS_TOK is ")"
    True
    >>>

"""


def _is_identifier(token: str) -> bool:
    return bool(
        LICENSE_EXPRESSION_IDENTIFIER_PATTERN.fullmatch(token)
        or INDIRECT_LICENSE_EXPRESSION_REF_PATTERN.fullmatch(token)
        or DOCUMENT_LICENSE_EXPRESSION_REF_PATTERN.fullmatch(token)
    )


def _tokenize(expression: str) -> Union[list[str], None]:
    """Split a license expression into tokens, or return `None` if invalid.

    The tokenizer scans `expression` from left to right using
    `LICENSE_EXPRESSION_TOKEN_PATTERN`. Each match must be either a
    parenthesis or a token accepted by `_is_identifier`. On the first
    unmatched or invalid token, tokenization fails and returns `None`.
    If the entire expression is consumed, the matched tokens are returned
    in order. An empty expression also returns `None`.

    This function only checks tokenization; it does not validate whether
    parentheses are balanced or whether the resulting tokens form a
    syntactically valid license expression.

    Args:
        expression: The license-expression text to tokenize.

    Returns:
        A list of tokens in their original order, or `None` if the
        expression is empty or contains an unmatched or invalid token.

    Testing:
        A single identifier produces a one-item list:

        >>> _tokenize("MIT")
        ['MIT']

        Parentheses are preserved as tokens:

        >>> _tokenize("(MIT)")
        ['(', 'MIT', ')']

        Multiple identifiers are returned in order when separated by
        syntax accepted by the configured token pattern:

        >>> _tokenize("MIT OR Apache-2.0")
        ['MIT', 'OR', 'Apache-2.0']

        An empty input has no tokens:

        >>> _tokenize("")
        >>> _tokenize("") is None
        True

        If the pattern cannot match the input at the current position,
        tokenization fails:

        >>> _tokenize("\\x00") is None
        True

        If the pattern recognizes a token that is not a parenthesis or a
        valid identifier, tokenization fails. This example assumes the
        configured pattern matches `"123"` as a token and
        `_is_identifier("123")` returns `False`:

        >>> _tokenize("$ and 123& # stuff") is None
        True
        >>>

    """
    tokens: list[str] = []
    position = 0
    while position < len(expression):
        match = LICENSE_EXPRESSION_TOKEN_PATTERN.match(expression, position)
        # This condition is defensive: But may not actually be needed.
        if match is None:  # pragma: no cover
            return None
        token = match.group(1)
        if token not in (
            _OPN_TOK,  # e.g., literal (
            _CLS_TOK,  # e.g., literal )
        ) and not _is_identifier(token):
            return None
        tokens.append(token)
        position = match.end()
    return tokens or None


class _ExpressionParser:
    """Recursive-descent parser with SPDX precedence: WITH, AND, then OR."""

    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.position = 0

    def _peek(self) -> Union[str, None]:
        if self.position >= len(self.tokens):
            return None
        return self.tokens[self.position]

    def _take(self) -> str:
        token = self._peek()
        if token is None:
            raise ValueError("unexpected end of SPDX expression")
        self.position += 1
        return token

    def parse(self) -> tuple[str, ...]:
        identifiers = self._parse_or()
        if self._peek() is not None:
            raise ValueError("trailing tokens in SPDX expression")
        # Keep the first spelling/order for diagnostics while avoiding duplicate
        # operands from expressions such as ``MIT OR MIT``.
        return tuple(dict.fromkeys(identifiers))

    def _parse_or(self) -> list[str]:
        identifiers = self._parse_and()
        while (token := self._peek()) is not None and token.upper() == _OR:
            self._take()
            identifiers.extend(self._parse_and())
        return identifiers

    def _parse_and(self) -> list[str]:
        identifiers = self._parse_with()
        while (token := self._peek()) is not None and token.upper() == _AND:
            self._take()
            identifiers.extend(self._parse_with())
        return identifiers

    def _parse_with(self) -> list[str]:
        identifiers, simple_license = self._parse_primary()
        token = self._peek()
        if token is not None and token.upper() == _WITH:
            if not simple_license:
                raise ValueError("WITH must modify a license identifier")
            self._take()
            exception = self._take()
            if not _is_identifier(exception) or exception in (
                _OPN_TOK,  # e.g., literal (
                _CLS_TOK,  # e.g., literal )
            ):  # pragma: no cover
                raise ValueError("invalid SPDX exception identifier")
            # Exceptions are modifiers and are deliberately not allow-list items.
        return identifiers

    def _parse_primary(self) -> tuple[list[str], bool]:
        """Parse one primary SPDX expression.

        A primary is either a license identifier or a parenthesized expression.
        The returned tuple contains the identifiers parsed and a boolean that is
        true only when the primary was a single, ungrouped identifier.

        Raises:
            ValueError: If the token is a reserved operator or closing
                parenthesis where an identifier is expected, if it is not a valid
                SPDX identifier, or if a parenthesized expression is not closed.

        Returns:
            A pair `(identifiers, is_simple_identifier)`. Parenthesized
            expressions return the identifiers from the inner expression and
            `False` for the second value.

        Doctests:

            >>> type(_ExpressionParser) != None
            True
            >>> type(_ExpressionParser) != type(None)
            True
            >>>

            >>> from types import SimpleNamespace
            >>> parser = SimpleNamespace(_take=iter(["MIT"]).__next__)
            >>> _ExpressionParser._parse_primary(parser)
            (['MIT'], True)

        A parenthesized expression delegates parsing to `_parse_or`:

            >>> parser = SimpleNamespace(
            ...     _take=iter(["(", ")"]).__next__,
            ...     _parse_or=lambda: ["MIT"],
            ... )
            >>> _ExpressionParser._parse_primary(parser)
            (['MIT'], False)

            >>> from types import SimpleNamespace
            >>> def parser(tokens, parsed=None):
            ...     p = SimpleNamespace(_take=iter(tokens).__next__)
            ...     if parsed is not None:
            ...         p._parse_or = lambda: parsed
            ...     return p

        A single identifier is returned as a simple primary:

            >>> _ExpressionParser._parse_primary(parser(["MIT"]))
            (['MIT'], True)

        A parenthesized expression returns the inner identifiers and is not
        considered a simple primary:

            >>> _ExpressionParser._parse_primary(parser(["(", ")"], ["MIT"]))
            (['MIT'], False)

        A group without a closing parenthesis is rejected:

            >>> _ExpressionParser._parse_primary(parser(["(", "AND"], ["MIT"]))
            Traceback (most recent call last):
            ...
            ValueError: unclosed SPDX expression group

        A closing parenthesis or reserved operator cannot start a primary:

            >>> _ExpressionParser._parse_primary(parser([")"]))
            Traceback (most recent call last):
            ...
            ValueError: expected SPDX license identifier
            >>> _ExpressionParser._parse_primary(parser(["AND"]))
            Traceback (most recent call last):
            ...
            ValueError: expected SPDX license identifier
            >>> _ExpressionParser._parse_primary(parser(["OR"]))
            Traceback (most recent call last):
            ...
            ValueError: expected SPDX license identifier
            >>> _ExpressionParser._parse_primary(parser(["WITH"]))
            Traceback (most recent call last):
            ...
            ValueError: expected SPDX license identifier

        A token that is not a valid identifier is rejected:

            >>> _ExpressionParser._parse_primary(parser(["???"]))
            Traceback (most recent call last):
            ...
            ValueError: invalid SPDX license identifier

        """
        token = self._take()
        if token == _OPN_TOK:  # e.g., literal (
            identifiers = self._parse_or()
            if self._take() != _CLS_TOK:  # e.g., literal )
                raise ValueError("unclosed SPDX expression group")
            return identifiers, False
        if token == _CLS_TOK or token.upper() in (_AND, _OR, _WITH):
            raise ValueError("expected SPDX license identifier")
        if not _is_identifier(token):
            raise ValueError("invalid SPDX license identifier")
        return [token], True


def parse_spdx_expression(expression: str) -> Union[tuple[str, ...], None]:
    """Return all license identifiers in a complete SPDX expression.

    ``WITH`` exception identifiers are omitted. Returns ``None`` for invalid or
    unsupported input, allowing callers to compare the original string exactly.
    """
    tokens = _tokenize(expression)
    if tokens is None:
        return None
    try:
        return _ExpressionParser(tokens).parse()
    except (ValueError, RecursionError):
        # A deeply nested or malformed string is legacy text, not a partial
        # expression. Never expose a prefix parse to matching code.
        return None


__all__ = ["parse_spdx_expression"]
