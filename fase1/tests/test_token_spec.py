"""Tests for the formal token definition (regexes in compiler/tokens.py).

The key test compares the hand-written lexer against a reference
tokenizer built ONLY from the regexes: on valid programs both must
produce exactly the same tokens.
"""

from pathlib import Path

import pytest

from compiler.lexer import tokenize
from compiler.tokens import (
    DELIMITERS,
    DOUBLE_OPERATORS,
    KEYWORDS,
    MASTER_PATTERN,
    SINGLE_OPERATORS,
    TOKEN_PATTERNS,
    TokenType as T,
    classify,
)

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def regex_tokenize(source: str) -> list[tuple[T, str, int, int]]:
    """Reference tokenizer: uses only MASTER_PATTERN. Valid input only."""
    tokens = []
    pos, line, line_start = 0, 1, 0
    while pos < len(source):
        m = MASTER_PATTERN.match(source, pos)
        assert m, f"no token matches at {source[pos:pos + 10]!r}"
        type_ = TOKEN_PATTERNS[m.lastindex - 1][0]
        lexeme = m.group()
        if type_ is not None:
            if type_ is T.ID:
                type_ = KEYWORDS.get(lexeme, T.ID)
            tokens.append((type_, lexeme, line, pos - line_start + 1))
        for i, c in enumerate(lexeme):  # keep line/column up to date
            if c == "\n":
                line, line_start = line + 1, pos + i + 1
        pos = m.end()
    return tokens


def lexer_tokens(source: str) -> list[tuple[T, str, int, int]]:
    tokens, errors = tokenize(source)
    assert errors == []
    return [(t.type, t.lexeme, t.line, t.column) for t in tokens if t.type is not T.EOF]


# ---------------------------------------------------------------------------
# classify(): one lexeme at a time
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("lexeme, expected", [
    *KEYWORDS.items(),
    *DOUBLE_OPERATORS.items(),
    *SINGLE_OPERATORS.items(),
    *DELIMITERS.items(),
    ("x", T.ID), ("_total2", T.ID), ("enteros", T.ID), ("si_", T.ID), ("Entero", T.ID),
    ("0", T.INT_LITERAL), ("42", T.INT_LITERAL), ("007", T.INT_LITERAL),
    ("3.14", T.REAL_LITERAL), ("0.0", T.REAL_LITERAL),
])
def test_classify_valid(lexeme, expected):
    assert classify(lexeme) is expected


@pytest.mark.parametrize("lexeme", [
    "12.3.4", "3abc", "12.", ".5", "@", "&", "|", "x y", "", "ñandú", "// c", "/* c */", " ",
])
def test_classify_not_a_single_token(lexeme):
    assert classify(lexeme) is None


def test_every_token_type_has_a_definition():
    defined = {type_ for type_, _ in TOKEN_PATTERNS if type_ is not None} | set(KEYWORDS.values())
    assert defined == set(T) - {T.EOF}


# ---------------------------------------------------------------------------
# Lexer vs. regex definition
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("source", [
    "entero x = 5;",
    "a==b=c!=!d<=e<f>=g>h&&i||j",
    "x/y // comentario\n/* bloque\n de dos líneas */ z",
    "real r = 3.14 * (2 + 0.5);",
    "enteros sino_ si mientras imprimir verdadero falso",
])
def test_lexer_matches_regex_definition(source):
    assert lexer_tokens(source) == regex_tokenize(source)


@pytest.mark.parametrize("name", ["valid.esp", "scopes.esp"])
def test_lexer_matches_regex_definition_on_examples(name):
    source = (EXAMPLES / name).read_text(encoding="utf-8")
    assert lexer_tokens(source) == regex_tokenize(source)
