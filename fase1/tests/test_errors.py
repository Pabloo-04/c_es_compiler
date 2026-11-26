"""Tests for the shared diagnostic format (errors.py)."""

import pytest

from compiler.errors import (
    CompileError,
    CompileWarning,
    LexicalError,
    SemanticError,
    sort_by_position,
)


def test_single_format():
    e = SemanticError(7, 3, "variable 'y' no declarada")
    assert str(e) == "Línea 7, columna 3: variable 'y' no declarada"


def test_same_format_for_every_kind():
    for cls in (LexicalError, SemanticError, CompileWarning):
        assert str(cls(1, 2, "x")) == "Línea 1, columna 2: x"


def test_labeled():
    assert LexicalError(2, 5, "carácter inválido '@'").labeled() == (
        "[error léxico] Línea 2, columna 5: carácter inválido '@'"
    )
    assert CompileWarning(4, 1, "m").labeled().startswith("[advertencia] ")


def test_hierarchy():
    assert isinstance(LexicalError(1, 1, ""), CompileError)
    assert isinstance(SemanticError(1, 1, ""), CompileError)
    assert not isinstance(CompileWarning(1, 1, ""), CompileError)
    assert LexicalError.is_error and not CompileWarning.is_error


def test_equality_depends_on_kind():
    assert LexicalError(1, 1, "m") == LexicalError(1, 1, "m")
    assert LexicalError(1, 1, "m") != SemanticError(1, 1, "m")


def test_immutable():
    with pytest.raises(AttributeError):
        SemanticError(1, 1, "m").line = 2


def test_sort_by_position():
    a, b, c = SemanticError(3, 1, "a"), LexicalError(1, 9, "b"), CompileWarning(1, 2, "c")
    assert sort_by_position([a, b, c]) == [c, b, a]
