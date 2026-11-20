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


def test_undeclared_inside_an_expression():
    errors = errors_of("entero y = w + 1 ;")
    assert errors == ["Línea 1, columna 12: variable 'w' no declarada"]


def test_self_reference_in_declaration():
    # The right-hand side is checked BEFORE x exists.
    errors = errors_of("entero x = x ;")
    assert errors == ["Línea 1, columna 12: variable 'x' no declarada"]


def test_self_reference_uses_the_outer_variable():
    # Inside the block, the x on the right is still the global one.
    program = """
entero x = 1 ;
si ( verdadero ) {
    entero x = x + 1 ;
    imprimir ( x ) ;
}
"""
    assert errors_of(program) == []


def test_extra_closing_brace():
    errors = errors_of("""
entero x = 1 ;
}
""")
    assert len(errors) == 1
    assert errors[0].startswith("Línea 2,")
    assert "'}'" in errors[0]


def test_unclosed_block():
    errors = errors_of("""
si ( verdadero ) {
    entero x = 1 ;
""")
    assert len(errors) == 1
    assert errors[0].startswith("Línea 1,")
    assert "falta cerrar" in errors[0]


def test_unclosed_nested_blocks_one_error_each():
    errors = errors_of("""
si ( verdadero ) {
    mientras ( falso ) {
""")
    assert [e.split(",")[0] for e in errors] == ["Línea 1", "Línea 2"]


def test_sibling_blocks_do_not_share_variables():
    errors = errors_of("""
si ( verdadero ) {
    entero a = 1 ;
} sino {
    a = 2 ;
}
""")
    assert len(errors) == 1
    assert "'a' no declarada" in errors[0]


def test_same_name_in_sibling_blocks_is_not_a_redeclaration():
    program = """
si ( verdadero ) {
    entero a = 1 ;
    imprimir ( a ) ;
}
mientras ( falso ) {
    entero a = 2 ;
    imprimir ( a ) ;
}
"""
    assert errors_of(program) == []


def test_redeclaration_in_inner_scope():
    errors = errors_of("""
si ( verdadero ) {
    entero a = 1 ;
    real a = 2.0 ;
}
""")
    assert len(errors) == 1
    assert "ya declarada en este ámbito (línea 2)" in errors[0]


def test_outer_variable_is_visible_in_nested_blocks():
    program = """
entero x = 1 ;
si ( x > 0 ) {
    mientras ( x < 5 ) {
        x = x + 1 ;
    }
}
"""
    assert errors_of(program) == []


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


def test_int_to_real_is_allowed():
    # Team decision (type_rules.is_assignable): entero -> real is a widening.
    assert errors_of("real x = 5 ;") == []


def test_real_to_int_is_not_allowed():
    assert errors_of("entero x = 2.5 ;") == ["Línea 1, columna 12: no se puede asignar real a entero"]


def test_bool_and_numbers_do_not_mix():
    assert len(errors_of("real r = verdadero ;")) == 1
    assert len(errors_of("bool b = 1 ;")) == 1


def test_relational_operators_give_bool():
    for op in ["<", ">", "<=", ">="]:
        assert errors_of(f"bool b = 1 {op} 2.5 ;") == [], op
        assert len(errors_of(f"entero e = 1 {op} 2 ;")) == 1, op


def test_relational_with_bool_is_an_error():
    assert len(errors_of("bool b = verdadero < 1 ;")) == 1


def test_equality_gives_bool():
    assert errors_of("bool b = 1 == 2 ;") == []
    assert errors_of("bool b = verdadero != falso ;") == []


def test_unary_not():
    assert errors_of("bool b = ! verdadero ;") == []
    assert len(errors_of("bool b = ! 1 ;")) == 1


def test_unary_minus():
    assert errors_of("entero e = - 5 ;") == []
    assert errors_of("real r = - 2.5 ;") == []
    assert len(errors_of("bool b = - verdadero ;")) == 1


def test_arithmetic_with_bool_is_an_error():
    assert len(errors_of("entero e = 1 + verdadero ;")) == 1


def test_parenthesized_condition():
    program = """
entero x = 1 ;
si ( ( x > 0 ) && ! ( x == 5 ) ) {
}
"""
    assert errors_of(program) == []


def test_assignment_type_is_checked():
    errors = errors_of("""
entero x = 1 ;
x = falso ;
""")
    assert errors == ["Línea 2, columna 5: no se puede asignar bool a entero"]


def test_several_errors_are_all_reported():
    program = """
entero x = verdadero ;
entero y = 1 ;
entero y = 2 ;
z = 3 ;
si ( y ) {
}
mientras ( y + 1 ) {
}
"""
    errors = errors_of(program)
    assert [e.split(",")[0] for e in errors] == [
        "Línea 1", "Línea 3", "Línea 4", "Línea 5", "Línea 7",
    ]


def test_errors_do_not_stop_the_analysis():
    # After an error, later valid code is still analyzed (and later errors found).
    errors = errors_of("""
a = 1 ;
entero b = 1 ;
imprimir ( b ) ;
c = 2 ;
""")
    assert len(errors) == 2
    assert "'a'" in errors[0] and "'c'" in errors[1]
