"""Integration tests: lexer + semantic analyzer + main.py together.  Owner: P5.

Unlike the other files, these run the WHOLE pipeline on the real example
programs in examples/, the same way the video demo does.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from compiler.lexer import tokenize
from compiler.semantic import SemanticAnalyzer

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"


def compile_source(source: str):
    """Run both phases like main.py does. Returns (lexical, semantic, warnings)."""
    tokens, lexical = tokenize(source)
    if lexical:
        return lexical, [], []
    analyzer = SemanticAnalyzer()
    analyzer.analyze(tokens)
    return lexical, analyzer.errors, analyzer.warnings


def compile_example(name: str):
    return compile_source((EXAMPLES / name).read_text(encoding="utf-8"))


def lines(diagnostics) -> list[int]:
    return sorted(d.line for d in diagnostics)


def run_main(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Example programs, end to end
# ---------------------------------------------------------------------------
def test_valid_example_is_clean():
    lexical, semantic, warnings = compile_example("valid.esp")
    assert lexical == [] and semantic == [] and warnings == []


def test_scopes_example_only_warns_about_shadowing():
    lexical, semantic, warnings = compile_example("scopes.esp")
    assert lexical == [] and semantic == []
    assert len(warnings) == 2
    assert all("oculta" in w.message for w in warnings)


def test_lexical_errors_example_stops_before_semantic():
    lexical, semantic, _ = compile_example("lexical_errors.esp")
    assert lines(lexical) == [3, 4, 5, 6, 7]
    assert semantic == []


def test_semantic_errors_example():
    # Every line marked in the file has exactly one error.
    lexical, semantic, _ = compile_example("semantic_errors.esp")
    assert lexical == []
    assert lines(semantic) == [2, 4, 5, 6, 9, 10]


@pytest.mark.parametrize("name", sorted(p.name for p in EXAMPLES.glob("*.esp")))
def test_every_example_runs_without_crashing(name):
    compile_example(name)


def test_program_with_comments_everywhere():
    source = """
// declaraciones
entero /* tipo */ x = 1; // valor inicial
/* bloque
   de varias líneas */
si (x > 0) { imprimir(x); }
"""
    lexical, semantic, _ = compile_source(source)
    assert lexical == [] and semantic == []


def test_lexer_positions_reach_semantic_messages():
    # The real lexer's line/column must show up in the semantic error.
    _, semantic, _ = compile_source("entero x = 1;\n\n    y = x;")
    assert [str(e) for e in semantic] == ["Línea 3, columna 5: variable 'y' no declarada"]


def test_warning_for_unused_variable():
    _, semantic, warnings = compile_source("entero x = 1;")
    assert semantic == []
    assert [w.message for w in warnings] == ["variable 'x' declarada pero nunca usada"]


def test_warning_for_uninitialized_variable():
    _, semantic, warnings = compile_source("entero x;\nimprimir(x);")
    assert semantic == []
    assert any("sin inicializar" in w.message for w in warnings)


# ---------------------------------------------------------------------------
# main.py (command line)
# ---------------------------------------------------------------------------
def test_main_exit_code_0_for_valid_program():
    result = run_main("examples/valid.esp")
    assert result.returncode == 0
    assert "Programa correcto" in result.stdout


def test_main_exit_code_1_for_semantic_errors():
    result = run_main("examples/semantic_errors.esp")
    assert result.returncode == 1
    assert "no se puede asignar bool a entero" in result.stdout


def test_main_exit_code_1_for_lexical_errors():
    result = run_main("examples/lexical_errors.esp")
    assert result.returncode == 1
    assert "no se ejecutó" in result.stdout


def test_main_exit_code_2_for_missing_file():
    result = run_main("examples/no_existe.esp")
    assert result.returncode == 2
    assert "No se pudo leer" in result.stderr


def test_main_tokens_option():
    result = run_main("examples/valid.esp", "--tokens")
    assert result.returncode == 0
    assert "contador" in result.stdout


def test_main_symbols_option():
    result = run_main("examples/scopes.esp", "--simbolos")
    assert result.returncode == 0
    for type_ in ("entero", "real", "bool"):
        assert type_ in result.stdout


def test_main_lexer_only():
    result = run_main("examples/semantic_errors.esp", "--lexer-only")
    # The file has no lexical errors, and the semantic phase is skipped.
    assert result.returncode == 0
    assert "no declarada" not in result.stdout
