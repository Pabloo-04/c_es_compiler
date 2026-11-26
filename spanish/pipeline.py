"""Pipeline: lexer -> parser -> agreement -> visualization.  Owner: Person 2.

    python -m spanish.pipeline "Ella come una manzana."
    python -m spanish.pipeline "Ella come una manzana." --tokens --arbol
    python -m spanish.pipeline "Ella come una manzana." --png results/figures/ella.png
    python -m spanish.pipeline --archivo oraciones.txt      # one sentence per line

From Python (the notebooks and evaluation/run_parser.py use this):

    from spanish.pipeline import analyze
    result = analyze("Ella come una manzana.")
    result.accepted, result.tree, result.errors, result.tags, result.subject

Same flow as Phase 1: if a phase fails, the next one does not run (a sentence
with invalid characters is not parsed; a sentence that does not parse is not
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
        """"sintactico" | "concordancia" | None (the "tipo_error" of the results)."""
        return self.errors[0].error_type if self.errors else None

    # The fields below follow docs/gramatica_es.md, 2.4: they exist when the
    # sentence parsed (accepted, or rejected only by agreement); otherwise None.
    @property
    def tags(self) -> list[list[str]] | None:
        """[["ella", "Prn"], ["come", "Verb"], ...], lowercase words."""
        if self.tree is None:
            return None
        return [[leaf.word.lower(), leaf.label] for leaf in self.tree.leaves()]

    @property
    def subject(self) -> str | None:
        from .agreement import subject_head

        return _word(subject_head(self.tree)) if self.tree else None

    @property
    def verb(self) -> str | None:
        from .agreement import main_verb

        return _word(main_verb(self.tree)) if self.tree else None

    @property
    def object(self) -> str | None:
        """Head of the direct object (the NP right under VP), "" if there is none."""
        if self.tree is None:
            return None
        vp = self.tree.child("VP")
        np = vp.child("NP") if vp else None
        base = np.child("NPbase") if np else None
        if base is None:
            return ""
        head = base.child("Prn") or (base.child("Nom").child("Noun") if base.child("Nom") else None)
        return _word(head)

    @property
    def pp_attachment(self) -> str | None:
        """What the FIRST PP attaches to: "sustantivo" | "verbo" | None (no PP or no tree)."""
        return pp_attachment(self.tree) if self.tree is not None else None


def pp_attachment(tree: Node) -> str | None:
    """"sustantivo" if the first PP (left to right) hangs from an NP, "verbo" if
    it hangs from the VP, None if the sentence has no PP.

    With the flattened trees, NP → NPbase PP* and VP → Verb NP? (PP | Adv)*, so
    the PP's parent says where it attached. The parser never answers "ambigua":
    it always attaches to the nearest noun phrase (docs/gramatica_es.md, 1.4).
    """
    def visit(node: Node, parent: Node | None):
        if node.label == "PP" and parent is not None:
            return {"NP": "sustantivo", "VP": "verbo"}.get(parent.label)
        for child in node.children:
            found = visit(child, node)
            if found is not None:
                return found
        return None

    return visit(tree, None)


def _word(leaf: Node | None) -> str:
    return leaf.word.lower() if leaf is not None and leaf.word else ""


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
        from .trees import ascii_tree

        print("\nÁrbol:")
        try:
            drawing = ascii_tree(result.tree)
        except (NotImplementedError, ImportError):
            drawing = result.tree.pretty()
        print(drawing)
        
    if result.tree is not None and args.png:
        from .trees import render

        # Pass the agreement errors so the words that break agreement are drawn in red.
        print(f"\nÁrbol guardado en {render(result.tree, args.png, errors=result.errors)}")
    if result.tree is not None:
        print(f"\nSujeto: {result.subject or '—'} · Verbo: {result.verb or '—'} · Objeto: {result.object or '—'}")
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
