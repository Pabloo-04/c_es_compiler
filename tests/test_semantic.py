"""Semantic analyzer tests.  Owner: Person 5 (with help from P3 and P4).

They use tokens_by_hand() so they do not depend on the lexer. Once the
lexer is ready, tokenize() can be used directly too.
"""

from compiler.semantic import analyze
from helpers import messages, tokens_by_hand


def errors_of(program: str) -> list[str]:
    return messages(analyze(tokens_by_hand(program)))


# ---------------------------------------------------------------------------
# Valid programs
# ---------------------------------------------------------------------------
def test_valid_program():
    program = """
entero x = 1 ;
real y = x + 2.5 ;
bool b = x < 10 ;
mientras ( b ) {
    x = x + 1 ;
    b = x < 10 ;
}
imprimir ( y ) ;
"""
    assert errors_of(program) == []


def test_shadowing_allowed():
    program = """
entero x = 1 ;
si ( verdadero ) {
    real x = 2.5 ;
}
"""
    assert errors_of(program) == []


# ---------------------------------------------------------------------------
# P3: symbol table and scopes
# ---------------------------------------------------------------------------
def test_undeclared_variable():
    errors = errors_of("x = 5 ;")
    assert len(errors) == 1
    assert errors[0].startswith("Línea 1,")
    assert "'x'" in errors[0]


def test_redeclaration_same_scope():
    errors = errors_of("""
entero x = 1 ;
entero x = 2 ;
""")
    assert len(errors) == 1
    assert errors[0].startswith("Línea 2,")


def test_variable_out_of_scope():
    errors = errors_of("""
si ( verdadero ) {
    entero z = 1 ;
}
z = 2 ;
""")
    assert len(errors) == 1
    assert errors[0].startswith("Línea 4,")


# TODO(P5): use inside an expression: `entero y = w + 1 ;` with w undeclared.
# TODO(P5): `entero x = x ;` -> x is undeclared.
# TODO(P5): unbalanced braces.


# ---------------------------------------------------------------------------
# P4: types
# ---------------------------------------------------------------------------
def test_assign_bool_to_int():
    errors = errors_of("entero x = verdadero ;")
    assert len(errors) == 1
    # The column is up to P4 (start of the declaration or of the value).
    assert errors[0].startswith("Línea 1, columna ")
    assert errors[0].endswith(": no se puede asignar bool a entero")


def test_int_plus_real_is_real():
    assert errors_of("real r = 1 + 2.5 ;") == []
    assert len(errors_of("entero e = 1 + 2.5 ;")) == 1


def test_if_condition_must_be_bool():
    errors = errors_of("""
entero x = 1 ;
si ( x ) {
}
""")
    assert len(errors) == 1
    assert errors[0].startswith("Línea 2,")


def test_while_condition_must_be_bool():
    errors = errors_of("""
mientras ( 1 + 2 ) {
}
""")
    assert len(errors) == 1


def test_logical_operation_with_int():
    assert len(errors_of("bool b = 1 && verdadero ;")) == 1


# TODO(P5): `real x = 5 ;` (depending on the team's decision in type_rules.is_assignable).
# TODO(P5): relational, equality, unary ! and -.
# TODO(P5): several errors in one program are all reported.
