"""Lexer tests.  Owner: Person 5 (with help from P2)."""

from pathlib import Path

from compiler.lexer import tokenize
from compiler.tokens import TokenType as T

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


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


# Delimiters, "x/y" and valid.esp without errors are covered in test_lexerV2.py.
# These cases complement them.

def test_delimiters_with_positions():
    tokens, errors = tokenize("si (x) { y; }")
    assert errors == []
    assert [(t.lexeme, t.column) for t in tokens[:-1]] == [
        ("si", 1), ("(", 4), ("x", 5), (")", 6), ("{", 8), ("y", 10), (";", 11), ("}", 13),
    ]


def test_comma_is_a_delimiter():
    assert types_of("a, b") == [T.ID, T.COMMA, T.ID, T.EOF]


def test_division_versus_line_comment():
    # "x / y" is a division; "x // y" is x followed by a comment.
    assert types_of("x / y") == [T.ID, T.SLASH, T.ID, T.EOF]
    assert types_of("x // y") == [T.ID, T.EOF]


def test_division_versus_block_comment():
    assert types_of("x /* y */ / z") == [T.ID, T.SLASH, T.ID, T.EOF]


def test_block_comment_is_not_nested():
    # Block comments end at the FIRST "*/", as in C.
    assert types_of("/* a /* b */ x") == [T.ID, T.EOF]


def test_lines_are_counted_inside_block_comments():
    tokens, _ = tokenize("/* uno\ndos\ntres */ entero")
    assert (tokens[0].lexeme, tokens[0].line) == ("entero", 3)


def test_every_keyword():
    source = "entero real bool si sino mientras imprimir verdadero falso"
    assert types_of(source) == [
        T.INT, T.REAL, T.BOOL, T.IF, T.ELSE, T.WHILE, T.PRINT, T.TRUE, T.FALSE, T.EOF,
    ]


def test_keywords_are_case_sensitive():
    assert types_of("Entero SI") == [T.ID, T.ID, T.EOF]


def test_identifiers_with_underscore_and_digits():
    tokens, errors = tokenize("_x x_1 var2")
    assert errors == []
    assert [(t.type, t.lexeme) for t in tokens[:-1]] == [
        (T.ID, "_x"), (T.ID, "x_1"), (T.ID, "var2"),
    ]


def test_operators_without_spaces():
    assert types_of("a<=b&&!c") == [T.ID, T.LESS_EQUAL, T.ID, T.AND, T.NOT, T.ID, T.EOF]


def test_triple_equals_is_equal_then_assign():
    # Longest match first: "===" -> "==" "=".
    assert types_of("===") == [T.EQUAL, T.ASSIGN, T.EOF]


def test_tabs_and_windows_newlines():
    tokens, errors = tokenize("entero\tx;\r\nreal y;")
    assert errors == []
    assert (tokens[3].lexeme, tokens[3].line) == ("real", 2)


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


# Lone "&"/"|" together and errors on different lines are in test_lexerV2.py.

def test_lone_pipe_is_invalid():
    _, errors = tokenize("bool b = a | c;")
    assert len(errors) == 1
    assert "'|'" in errors[0].message


def test_lone_ampersand_is_invalid():
    _, errors = tokenize("bool b = a & c;")
    assert len(errors) == 1
    assert "'&'" in errors[0].message


def test_errors_on_several_lines_with_columns():
    source = "entero a = 1;\n  @\nreal r = 1.2.3;\n#"
    _, errors = tokenize(source)
    assert [(e.line, e.column) for e in errors] == [(2, 3), (3, 10), (4, 1)]


def test_valid_tokens_survive_around_an_error():
    tokens, errors = tokenize("entero x = 5 @ 3;")
    assert len(errors) == 1
    assert [t.type for t in tokens] == [
        T.INT, T.ID, T.ASSIGN, T.INT_LITERAL, T.INT_LITERAL, T.SEMICOLON, T.EOF,
    ]


def test_lexical_errors_example():
    _, errors = tokenize((EXAMPLES / "lexical_errors.esp").read_text(encoding="utf-8"))
    assert [e.line for e in errors] == [3, 4, 5, 6, 7]
