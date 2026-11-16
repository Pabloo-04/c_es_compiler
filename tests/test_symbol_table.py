"""Symbol table unit tests.  Owner: P5 (with help from P3)."""

from compiler.symbol_table import Symbol, SymbolTable


def sym(name: str, type_: str = "entero", line: int = 1) -> Symbol:
    return Symbol(name, type_, line, 1)


def test_declare_and_lookup():
    table = SymbolTable()
    assert table.declare(sym("x")) is None
    assert table.lookup("x").type == "entero"


def test_undeclared():
    assert SymbolTable().lookup("y") is None


def test_redeclaration_same_scope():
    table = SymbolTable()
    table.declare(sym("x", line=1))
    previous = table.declare(sym("x", line=5))
    assert previous is not None and previous.line == 1


def test_shadowing_in_inner_scope():
    table = SymbolTable()
    table.declare(sym("x", "entero"))
    table.open_scope()
    assert table.declare(sym("x", "real")) is None
    assert table.lookup("x").type == "real"
    table.close_scope()
    assert table.lookup("x").type == "entero"


def test_inner_variable_does_not_exist_outside():
    table = SymbolTable()
    table.open_scope()
    table.declare(sym("z"))
    table.close_scope()
    assert table.lookup("z") is None


def test_depth():
    table = SymbolTable()
    assert table.depth == 0
    table.open_scope()
    assert table.depth == 1


# TODO(P5): three levels of nested scopes.
# TODO(P5): closing the global scope must not break the table.
