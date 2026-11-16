"""Lexer tests.  Owner: Person 5 (with help from P2)."""

from compiler.lexer import tokenize
from compiler.tokens import TokenType as T


def types_of(source: str) -> list[T]:
    tokens, _ = tokenize(source)
    return [t.type for t in tokens]


# ---------------------------------------------------------------------------
# Valid input
# ---------------------------------------------------------------------------
def test_simple_declaration():
    assert types_of("entero x = 5;") == [T.INT, T.ID, T.ASSIGN, T.INT_LITERAL, T.SEMICOLON, T.EOF]


def test_real_literal():
    tokens, errors = tokenize("3.14")
    assert errors == []
    assert tokens[0].type == T.REAL_LITERAL
    assert tokens[0].lexeme == "3.14"


def test_keyword_vs_identifier():
    # "enteros" and "si_" are identifiers, not keywords.
    assert types_of("entero enteros si si_") == [T.INT, T.ID, T.IF, T.ID, T.EOF]


def test_double_operators_before_single():
    assert types_of("== = != ! <= < >= > && ||") == [
        T.EQUAL, T.ASSIGN, T.NOT_EQUAL, T.NOT, T.LESS_EQUAL,
        T.LESS, T.GREATER_EQUAL, T.GREATER, T.AND, T.OR, T.EOF,
    ]


def test_line_and_column():
    tokens, _ = tokenize("entero x;\n  real y;")
    real = tokens[3]
    assert (real.lexeme, real.line, real.column) == ("real", 2, 3)


def test_comments_are_skipped():
    source = "// comentario\nentero /* en\nmedio */ x;"
    assert types_of(source) == [T.INT, T.ID, T.SEMICOLON, T.EOF]


def test_always_ends_with_eof():
    assert types_of("") == [T.EOF]


# TODO(P5): delimiters ( ) { } ; ,
# TODO(P5): the full examples/valid.esp program has no errors.
# TODO(P5): "x/y" gives ID SLASH ID (the "/" is not a comment).


# ---------------------------------------------------------------------------
# Lexical errors
# ---------------------------------------------------------------------------
def test_invalid_character():
    _, errors = tokenize("entero x = 5 @ 3;")
    assert len(errors) == 1
    assert errors[0].line == 1
    assert "@" in errors[0].message


def test_number_with_two_dots():
    _, errors = tokenize("real x = 12.3.4;")
    assert len(errors) == 1
    assert "12.3.4" in errors[0].message


def test_identifier_starting_with_digit():
    _, errors = tokenize("entero 3abc = 1;")
    assert len(errors) == 1
    assert "3abc" in errors[0].message


def test_unterminated_comment():
    _, errors = tokenize("entero x;\n/* nunca se cierra")
    assert len(errors) == 1
    assert errors[0].line == 2


def test_continues_after_an_error():
    # Team decision: collect errors and keep going.
    _, errors = tokenize("@ entero x; #")
    assert len(errors) == 2


# TODO(P5): lone "&" and "|" are invalid characters.
# TODO(P5): errors on different lines report the right line.
