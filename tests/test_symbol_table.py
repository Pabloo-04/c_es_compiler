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


def test_three_levels_of_nested_scopes():
    table = SymbolTable()
    table.declare(sym("x", "entero"))
    table.declare(sym("g", "bool"))
    table.open_scope()
    table.declare(sym("x", "real"))
    table.open_scope()
    table.declare(sym("x", "bool"))
    assert table.depth == 2
    assert table.lookup("x").type == "bool"
    assert table.lookup("g").type == "bool"   # global still visible from depth 2
    table.close_scope()
    assert table.lookup("x").type == "real"
    table.close_scope()
    assert table.lookup("x").type == "entero"
    assert table.depth == 0


def test_closing_the_global_scope_does_nothing():
    table = SymbolTable()
    table.declare(sym("x"))
    assert table.close_scope() is None
    assert table.depth == 0
    assert table.lookup("x") is not None
    # The table still works afterwards.
    table.open_scope()
    assert table.depth == 1


def test_close_scope_returns_its_symbols_in_order():
    table = SymbolTable()
    table.open_scope()
    table.declare(sym("b"))
    table.declare(sym("a"))
    assert [s.name for s in table.close_scope()] == ["b", "a"]


def test_redeclaration_keeps_the_first_symbol():
    table = SymbolTable()
    table.declare(sym("x", "entero", line=1))
    table.declare(sym("x", "real", line=2))
    assert table.lookup("x").type == "entero"


def test_redeclaration_only_checks_current_scope():
    table = SymbolTable()
    table.open_scope()
    table.declare(sym("x"))
    table.close_scope()
    # The inner x is gone, so declaring it in the global scope is fine.
    assert table.declare(sym("x")) is None


def test_lookup_returns_the_same_object():
    # semantic.py marks symbol.used = True on the object lookup() returns.
    table = SymbolTable()
    s = sym("x")
    table.declare(s)
    table.lookup("x").used = True
    assert s.used is True
