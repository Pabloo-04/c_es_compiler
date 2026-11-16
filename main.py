"""Compiler entry point (Phase 1).

Usage:
    python main.py examples/valid.esp               # lexer + semantic analysis
    python main.py examples/valid.esp --tokens      # also print the tokens
    python main.py examples/valid.esp --lexer-only

The program's output is in Spanish, like the language and its error messages.
"""

import argparse
import sys
from pathlib import Path

from compiler.lexer import tokenize
from compiler.semantic import analyze


def main() -> int:
    parser = argparse.ArgumentParser(description="Compilador Fase 1: lexer y analizador semántico")
    parser.add_argument("file", type=Path, help="programa fuente (.esp)")
    parser.add_argument("--tokens", action="store_true", help="imprimir la lista de tokens")
    parser.add_argument("--lexer-only", action="store_true", help="no correr el semántico")
    args = parser.parse_args()

    try:
        source = args.file.read_text(encoding="utf-8")
    except OSError as e:
        print(f"No se pudo leer {args.file}: {e}", file=sys.stderr)
        return 2

    tokens, lexical_errors = tokenize(source)

    if args.tokens or args.lexer_only:
        print("=== Tokens ===")
        for t in tokens:
            print(t)
        print()

    if lexical_errors:
        print("=== Errores léxicos ===")
        for e in lexical_errors:
            print(e)
        # With lexical errors there is no point in running the semantic phase.
        return 1

    if args.lexer_only:
        print("Análisis léxico sin errores.")
        return 0

    semantic_errors = analyze(tokens)
    if semantic_errors:
        print("=== Errores semánticos ===")
        for e in semantic_errors:
            print(e)
        return 1

    print("Programa correcto: sin errores léxicos ni semánticos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
