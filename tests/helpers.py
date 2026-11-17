"""Helpers for writing token lists by hand.

Until P2's lexer is ready, P3 and P4 can test the semantic analyzer like this:

    tokens = tokens_by_hand('''
        entero x = 1 ;
        si ( x > 0 ) {
            real x = 2.5 ;
        }
    ''')

Rules: tokens separated by spaces, and lines count from 1 (leading blank
lines are ignored). It does NOT support comments or lexical errors: that
is what the real lexer is for.
"""

import re

from compiler.tokens import (
    DELIMITERS,
    DOUBLE_OPERATORS,
    KEYWORDS,
    SINGLE_OPERATORS,
    Token,
    TokenType,
)

_FIXED = {**KEYWORDS, **DOUBLE_OPERATORS, **SINGLE_OPERATORS, **DELIMITERS}


def _type_of(lexeme: str) -> TokenType:
    if lexeme in _FIXED:
        return _FIXED[lexeme]
    if re.fullmatch(r"[0-9]+\.[0-9]+", lexeme):
        return TokenType.REAL_LITERAL
    if re.fullmatch(r"[0-9]+", lexeme):
        return TokenType.INT_LITERAL
    if re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", lexeme):
        return TokenType.ID
    raise ValueError(f"tokens_by_hand: unrecognized lexeme {lexeme!r}")


def tokens_by_hand(text: str) -> list[Token]:
    lines = text.strip("\n").splitlines()
    tokens: list[Token] = []
    for line_number, line in enumerate(lines, start=1):
        for m in re.finditer(r"\S+", line):
            tokens.append(Token(_type_of(m.group()), m.group(), line_number, m.start() + 1))
    tokens.append(Token(TokenType.EOF, "", len(lines) + 1, 1))
    return tokens


def messages(errors) -> list[str]:
    """Turn errors into "Línea N, columna M: ..." strings for easy comparison."""
    return [str(e) for e in errors]
