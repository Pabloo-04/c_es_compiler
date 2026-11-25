"""Compiler entry point (Phase 1).

Usage:
    python main.py examples/valid.esp                # lexer + semantic analysis
    python main.py examples/valid.esp --tokens       # also print the token table
    python main.py examples/valid.esp --simbolos     # also print the symbol table
    python main.py examples/valid.esp --tokens --simbolos
    python main.py examples/valid.esp --lexer-only

Flow: read the file -> lexer -> (only if there are no lexical errors) semantic.

The program's output is in Spanish, like the language and its error messages.
Exit code: 0 no errors (warnings allowed), 1 errors, 2 file could not be read.
"""

import argparse
import sys
from pathlib import Path

from compiler.errors import Diagnostic, sort_by_position
from compiler.lexer import tokenize
from compiler.semantic import SemanticAnalyzer
from compiler.symbol_table import Symbol
from compiler.tokens import Token

# ANSI colors, only when writing to a real terminal (not when redirected to a file).
USE_COLOR = sys.stdout.isatty()


def color(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def red(text: str) -> str:
    return color(text, "31")


def yellow(text: str) -> str:
    return color(text, "33")


def green(text: str) -> str:
    return color(text, "32")


def bold(text: str) -> str:
    return color(text, "1")


def title(text: str) -> None:
    print()
    print(bold(f"=== {text} ==="))


# ----------------------------------------------------------------------
# Tables
# ----------------------------------------------------------------------
def print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print rows as a text table with aligned columns."""
    widths = [len(h) for h in headers]
    for row in rows:
        widths = [max(w, len(cell)) for w, cell in zip(widths, row)]

    def line(cells: list[str]) -> str:
        return "  ".join(cell.ljust(w) for cell, w in zip(cells, widths)).rstrip()

    print(bold(line(headers)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(line(row))


def print_tokens(tokens: list[Token]) -> None:
    title(f"Tokens ({len(tokens)})")
    rows = [
        [str(t.line), str(t.column), t.type.name, repr(t.lexeme) if t.lexeme else ""]
        for t in tokens
    ]
    print_table(["Línea", "Col", "Tipo", "Lexema"], rows)


def print_symbols(declared: list[tuple[int, Symbol]]) -> None:
    title(f"Tabla de símbolos ({len(declared)})")
    if not declared:
        print("(sin variables declaradas)")
        return
    rows = [
        [
            "global" if depth == 0 else f"bloque {depth}",
            # Indent by depth so nested scopes and shadowing are visible at a glance.
            "  " * depth + s.name,
            s.type,
            f"{s.line}:{s.column}",
            "sí" if s.initialized else "no",
            "sí" if s.used else "no",
        ]
        for depth, s in declared
    ]
    print_table(["Ámbito", "Nombre", "Tipo", "Declarada", "Inicializada", "Usada"], rows)


def print_diagnostics(header: str, diagnostics: list[Diagnostic], paint) -> None:
    if not diagnostics:
        return
    title(f"{header} ({len(diagnostics)})")
    for d in sort_by_position(diagnostics):
        print(paint(str(d)))


# ----------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="Compilador Fase 1: lexer y analizador semántico")
    parser.add_argument("file", type=Path, help="programa fuente (.esp)")
    parser.add_argument("--tokens", action="store_true", help="mostrar la tabla de tokens")
    parser.add_argument("--simbolos", action="store_true", help="mostrar la tabla de símbolos")
    parser.add_argument("--lexer-only", action="store_true", help="correr solo el lexer")
    args = parser.parse_args()

    try:
        source = args.file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"No se pudo leer {args.file}: {e}", file=sys.stderr)
        return 2

    print(bold(f"Compilando {args.file}"))

    # --- Lexical phase -------------------------------------------------
    tokens, lexical_errors = tokenize(source)
    if args.tokens or args.lexer_only:
        print_tokens(tokens)

    if lexical_errors:
        print_diagnostics("Errores léxicos", lexical_errors, red)
        print()
        print(red("El análisis semántico no se ejecutó porque hay errores léxicos."))
        return 1

    if args.lexer_only:
        print()
        print(green("Análisis léxico sin errores."))
        return 0

    # --- Semantic phase ------------------------------------------------
    try:
        analyzer = SemanticAnalyzer()
        semantic_errors = analyzer.analyze(tokens)
    except NotImplementedError as e:
        # While P3/P4 have not finished, the lexer demo still works.
        print()
        print(yellow(f"Análisis semántico aún no implementado ({e})."))
        print(green("Análisis léxico sin errores."))
        return 0

    if args.simbolos:
        print_symbols(analyzer.declared)

    print_diagnostics("Errores semánticos", semantic_errors, red)
    print_diagnostics("Advertencias", analyzer.warnings, yellow)

    print()
    if semantic_errors:
        print(red(f"Compilación fallida: {len(semantic_errors)} error(es)."))
        return 1

    summary = "Programa correcto: sin errores léxicos ni semánticos"
    if analyzer.warnings:
        summary += f" ({len(analyzer.warnings)} advertencia(s))"
    print(green(summary + "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
