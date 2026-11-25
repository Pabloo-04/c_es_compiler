"""Pipeline: lexer -> parser -> agreement -> visualization.  Owner: Person 2.

    python -m spanish.pipeline "el gato negro come el pescado"
    python -m spanish.pipeline "el gato negro come el pescado" --tokens --arbol
    python -m spanish.pipeline "el gato negro come el pescado" --png results/figures/gato.png
    python -m spanish.pipeline --archivo oraciones.txt      # one sentence per line

From Python (the notebooks and evaluation/run_parser.py use this):

    from spanish.pipeline import analyze
    result = analyze("el gato come")
    result.accepted, result.tree, result.errors

Same flow as Phase 1: if a phase fails, the next one does not run (a sentence
with unknown words is not parsed; a sentence that does not parse is not
checked for agreement).

The base flow is implemented so everyone can use analyze() from day 1;
it works as soon as lexer, parser and agreement are implemented.
"""

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .errors import Diagnostic, sort_by_position
from .lexicon import Lexicon
from .tokens import Token
from .tree import Node


@dataclass
class Result:
    sentence: str
    tokens: list[Token] = field(default_factory=list)
    tree: Node | None = None
    errors: list[Diagnostic] = field(default_factory=list)

    @property
    def accepted(self) -> bool:
        return self.tree is not None and not self.errors

    @property
    def error_type(self) -> str | None:
        """"lexico" | "sintactico" | "concordancia" | None (for the results file)."""
        return self.errors[0].error_type if self.errors else None


_LEXICON: Lexicon | None = None


def analyze(sentence: str, lexicon: Lexicon | None = None) -> Result:
    # Imported here so that a NotImplementedError in one module does not
    # break `import spanish.pipeline`.
    from .agreement import check
    from .lexer import tokenize
    from .parser import parse

    global _LEXICON
    if lexicon is None:
        _LEXICON = _LEXICON or Lexicon.load()
        lexicon = _LEXICON

    result = Result(sentence)
    result.tokens, lexical_errors = tokenize(sentence, lexicon)
    if lexical_errors:
        result.errors = list(lexical_errors)
        return result

    tree, parse_errors = parse(result.tokens)
    if parse_errors or tree is None:
        result.errors = list(parse_errors)
        return result

    result.tree = tree
    result.errors = list(check(tree))
    return result


# ----------------------------------------------------------------------
# Command line
# ----------------------------------------------------------------------
def show(result: Result, args: argparse.Namespace) -> None:
    print(f"Oración: {result.sentence}")
    if args.tokens:
        print("\nPalabras:")
        for token in result.tokens:
            print(f"  {token}")
    if result.tree is not None and args.arbol:
        print("\nÁrbol:")
        print(result.tree.pretty())
        # TODO(P2/P3): use trees.ascii_tree(result.tree) once it is implemented.
    if result.tree is not None and args.png:
        from .trees import render

        print(f"\nÁrbol guardado en {render(result.tree, args.png)}")
    for error in sort_by_position(result.errors):
        print(f"  {error.labeled()}")
    print("ACEPTADA" if result.accepted else "RECHAZADA")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analizador de oraciones en español (Fase 2)")
    parser.add_argument("oracion", nargs="?", help="oración a analizar")
    parser.add_argument("--archivo", type=Path, help="archivo con una oración por línea")
    parser.add_argument("--tokens", action="store_true", help="mostrar palabras y rasgos")
    parser.add_argument("--arbol", action="store_true", help="mostrar el árbol")
    parser.add_argument("--png", type=Path, help="guardar el árbol como imagen")
    args = parser.parse_args()

    if args.archivo:
        sentences = [s.strip() for s in args.archivo.read_text(encoding="utf-8").splitlines() if s.strip()]
    elif args.oracion:
        sentences = [args.oracion]
    else:
        parser.error("falta la oración o --archivo")

    all_ok = True
    for i, sentence in enumerate(sentences):
        if i:
            print("-" * 60)
        try:
            result = analyze(sentence)
        except NotImplementedError as e:
            # While a phase is still a TODO, say which one instead of a traceback.
            print(f"Falta implementar una etapa del pipeline: {e}", file=sys.stderr)
            return 2
        show(result, args)
        all_ok = all_ok and result.accepted
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
