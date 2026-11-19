"""Tests for statements.py (grouping) and type_rules.py (types).  Owner: P4.

Separate file from test_semantic.py (P5) to avoid Git conflicts.
They use the real lexer, so the sources are written as normal code.
"""

import pytest

from compiler.lexer import tokenize
from compiler.semantic import SemanticAnalyzer
from compiler.statements import StatementType as S, group
from compiler.symbol_table import SymbolTable
from compiler.tokens import TokenType as T
from compiler.type_rules import (
    binary_type,
    expression_type,
    is_assignable,
    unary_type,
)


def analyze(source: str):
    tokens, lexical = tokenize(source)
    assert lexical == []
    a = SemanticAnalyzer()
    a.analyze(tokens)
    return [str(e) for e in a.errors], [str(w) for w in a.warnings]


def errors_of(source: str) -> list[str]:
    return analyze(source)[0]


def kinds(source: str) -> list[S]:
    tokens, _ = tokenize(source)
    statements, errors = group(tokens)
    assert errors == []
    return [s.type for s in statements]


# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------
def test_example_from_the_docstring():
    source = """
entero x = 1;
si (x > 0) {
    x = x + 1;
} sino {
    imprimir(x);
}
"""
    assert kinds(source) == [
        S.DECLARATION, S.IF, S.OPEN_BLOCK, S.ASSIGNMENT, S.CLOSE_BLOCK,
        S.ELSE, S.OPEN_BLOCK, S.PRINT, S.CLOSE_BLOCK,
    ]


def test_statement_fields():
    tokens, _ = tokenize("real y = 1 + 2;\nmientras (y < 3) { }")
    decl, loop, *_ = group(tokens)[0]
    assert decl.data_type.lexeme == "real" and decl.name.lexeme == "y"
    assert [t.lexeme for t in decl.expression] == ["1", "+", "2"]
    assert loop.type is S.WHILE and [t.lexeme for t in loop.expression] == ["y", "<", "3"]


def test_nested_parentheses_in_condition():
    tokens, errors = group(tokenize("si ((1 < 2) && verdadero) { }")[0])
    assert errors == []
    assert [t.lexeme for t in tokens[0].expression] == [
        "(", "1", "<", "2", ")", "&&", "verdadero"]


def test_missing_semicolon_does_not_swallow_next_statement():
    tokens, _ = tokenize("entero x = 1\nentero y = 2;")
    statements, errors = group(tokens)
    assert [str(e) for e in errors] == [
        "Línea 1, columna 13: falta ';' al final de la sentencia"]
    assert [s.name.lexeme for s in statements] == ["x", "y"]


def test_missing_closing_parenthesis():
    _, errors = group(tokenize("si (x > 0 {\n}")[0])
    assert len(errors) == 1 and "falta ')'" in errors[0].message


def test_stray_token_is_reported_and_recovered():
    tokens, _ = tokenize("+ 3;\nentero a = 1;")
    statements, errors = group(tokens)
    assert len(errors) == 1 and errors[0].line == 1
    assert [s.type for s in statements] == [S.DECLARATION]


def test_missing_equals_in_assignment():
    _, errors = group(tokenize("x 5;")[0])
    assert len(errors) == 1 and "se esperaba '='" in errors[0].message


def test_empty_condition():
    _, errors = group(tokenize("si () { }")[0])
    assert len(errors) == 1 and "vacía" in errors[0].message


# ---------------------------------------------------------------------------
# Type table
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("op, left, right, expected", [
    (T.PLUS, "entero", "entero", "entero"),
    (T.STAR, "entero", "real", "real"),
    (T.SLASH, "real", "entero", "real"),
    (T.MINUS, "real", "real", "real"),
    (T.PLUS, "bool", "entero", None),
    (T.LESS, "entero", "real", "bool"),
    (T.LESS, "bool", "bool", None),
    (T.EQUAL, "entero", "real", "bool"),
    (T.EQUAL, "bool", "bool", "bool"),
    (T.NOT_EQUAL, "bool", "entero", None),
    (T.AND, "bool", "bool", "bool"),
    (T.OR, "entero", "bool", None),
])
def test_binary_type(op, left, right, expected):
    assert binary_type(op, left, right) == expected


def test_unary_type():
    assert unary_type(T.NOT, "bool") == "bool"
    assert unary_type(T.NOT, "entero") is None
    assert unary_type(T.MINUS, "entero") == "entero"
    assert unary_type(T.MINUS, "real") == "real"
    assert unary_type(T.MINUS, "bool") is None


def test_is_assignable():
    assert is_assignable("entero", "entero")
    assert is_assignable("real", "entero")          # widening
    assert not is_assignable("entero", "real")      # would lose decimals
    assert not is_assignable("entero", "bool")
    assert not is_assignable("bool", "entero")


def type_of(source: str):
    tokens, _ = tokenize(source)
    errors: list = []
    return expression_type(tokens[:-1], SymbolTable(), errors), errors


def test_precedence_and_associativity():
    assert type_of("1 + 2 * 3.0")[0] == "real"
    assert type_of("1 < 2 && verdadero")[0] == "bool"
    assert type_of("!(1 < 2) || falso")[0] == "bool"
    assert type_of("-3 + 1")[0] == "entero"
    assert type_of("(1 + 2) * 3")[0] == "entero"


def test_invalid_operation_message():
    result, errors = type_of("1 && verdadero")
    assert result is None
    assert [str(e) for e in errors] == ["Línea 1, columna 3: operación inválida: entero && bool"]


def test_one_error_per_problem_no_cascade():
    # The inner error makes (1 + verdadero) unknown; the outer * adds nothing.
    _, errors = type_of("(1 + verdadero) * 2")
    assert len(errors) == 1


@pytest.mark.parametrize("source", ["1 +", "(1", "1 2", ")", "* 3", "1 + * 2"])
def test_syntax_problems_give_one_error(source):
    result, errors = type_of(source)
    assert result is None and len(errors) == 1


# ---------------------------------------------------------------------------
# Whole programs
# ---------------------------------------------------------------------------
def test_assign_bool_to_int():
    assert errors_of("entero x = verdadero;") == [
        "Línea 1, columna 12: no se puede asignar bool a entero"]


def test_int_to_real_is_allowed_but_not_the_reverse():
    assert errors_of("real x = 5;") == []
    assert errors_of("entero x = 2.5;") == [
        "Línea 1, columna 12: no se puede asignar real a entero"]


def test_int_plus_real_is_real():
    assert errors_of("real r = 1 + 2.5;") == []
    assert len(errors_of("entero e = 1 + 2.5;")) == 1


def test_assignment_type_mismatch():
    errors = errors_of("bool b = verdadero;\nb = 3;")
    assert errors == ["Línea 2, columna 5: no se puede asignar entero a bool"]


def test_conditions_must_be_bool():
    errors = errors_of("entero x = 1;\nsi (x) { }\nmientras (x + 1) { }")
    assert errors == [
        "Línea 2, columna 5: la condición de 'si' debe ser bool, pero es entero",
        "Línea 3, columna 11: la condición de 'mientras' debe ser bool, pero es entero",
    ]


def test_bool_conditions_are_fine():
    source = "entero x = 1;\nsi (x > 0 && !falso) { }\nmientras (x < 3) { x = x + 1; }"
    assert errors_of(source) == []


def test_undeclared_in_condition_is_reported_once():
    errors = errors_of("si (n > 0) { }")
    assert len(errors) == 1 and "'n' no declarada" in errors[0]


def test_undeclared_in_type_error_is_not_doubled():
    # w is undeclared: one error, no cascade of type errors.
    assert len(errors_of("entero y = w + 1;")) == 1


def test_print_accepts_any_type_but_checks_the_expression():
    assert errors_of("imprimir(1); imprimir(2.5); imprimir(verdadero);") == []
    assert len(errors_of("imprimir(1 + verdadero);")) == 1


def test_assignment_to_undeclared_still_checks_its_expression():
    errors = errors_of("z = 1 + verdadero;")
    assert len(errors) == 2


def test_else_needs_an_if():
    assert errors_of("entero x = 1;\nsi (x > 0) { } sino { }") == []
    assert errors_of("sino { }") == ["Línea 1, columna 1: 'sino' sin un 'si' correspondiente"]
    assert len(errors_of("mientras (verdadero) { } sino { }")) == 1


def test_valid_example_has_no_errors():
    from pathlib import Path
    source = (Path(__file__).resolve().parent.parent / "examples" / "valid.esp").read_text(
        encoding="utf-8")
    errors, _ = analyze(source)
    assert errors == []