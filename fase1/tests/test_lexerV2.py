"""Extra lexer tests written by P2 (separate file to avoid Git conflicts with P5)."""

from pathlib import Path

from compiler.lexer import tokenize
from compiler.tokens import TokenType as T

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def types_of(source):
    tokens, _ = tokenize(source)
    return [t.type for t in tokens]


def test_delimiters():
    assert types_of("( ) { } ; ,") == [
        T.LPAREN, T.RPAREN, T.LBRACE, T.RBRACE, T.SEMICOLON, T.COMMA, T.EOF]


def test_slash_is_not_a_comment():
    assert types_of("x/y") == [T.ID, T.SLASH, T.ID, T.EOF]


def test_valid_example_has_no_errors():
    tokens, errors = tokenize((EXAMPLES / "valid.esp").read_text(encoding="utf-8"))
    assert errors == []
    assert tokens[-1].type == T.EOF


def test_scopes_example_has_no_errors():
    _, errors = tokenize((EXAMPLES / "scopes.esp").read_text(encoding="utf-8"))
    assert errors == []


def test_lone_ampersand_and_pipe_are_invalid():
    _, errors = tokenize("a & b | c")
    assert len(errors) == 2
    assert "&" in errors[0].message and "|" in errors[1].message


def test_errors_report_their_own_line():
    _, errors = tokenize("entero a;\nentero b = 1 @ 2;\n\nreal c = 1.2.3;")
    assert [e.line for e in errors] == [2, 4]


def test_error_column_is_where_the_lexeme_starts():
    _, errors = tokenize("entero b = 7 @ 2;")
    assert (errors[0].line, errors[0].column) == (1, 14)


def test_trailing_dot_is_malformed():
    _, errors = tokenize("real x = 12.;")
    assert len(errors) == 1 and "12." in errors[0].message


def test_leading_dot_is_invalid_character():
    _, errors = tokenize("real x = .5;")
    assert len(errors) == 1 and "'.'" in errors[0].message


def test_number_glued_to_letters_after_real():
    _, errors = tokenize("real x = 3.5x;")
    assert len(errors) == 1 and "3.5x" in errors[0].message


def test_malformed_lexeme_produces_no_token():
    tokens, errors = tokenize("3abc")
    assert [t.type for t in tokens] == [T.EOF] and len(errors) == 1


def test_unterminated_comment_reports_where_it_started():
    _, errors = tokenize("entero x;\n  /* abierto\n sigue")
    assert (errors[0].line, errors[0].column) == (2, 3)
    assert "sin cerrar" in errors[0].message


def test_comment_at_end_without_newline():
    assert types_of("entero x; // fin") == [T.INT, T.ID, T.SEMICOLON, T.EOF]


def test_eof_position():
    tokens, _ = tokenize("a\nb")
    assert (tokens[-1].line, tokens[-1].column) == (2, 2)


def test_ascii_letters_only():
    _, errors = tokenize("entero ñ = 1;")
    assert len(errors) == 1 and "ñ" in errors[0].message


def test_garbage_does_not_hang():
    for s in ["@@@", "&&&&|||", "...", "12.3.4.5.6", "/*", "/", "3.", "\x00\x01"]:
        tokenize(s)