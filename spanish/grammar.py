"""The Spanish CFG as data.  Owner: Person 1.

Single source of truth for the grammar:
  - docs/gramatica_es.md explains it (P1).
  - parser.py implements it by hand, one method per non-terminal (P2).
  - experiments/prompts.py sends it to the LLM with as_bnf() (P5).
  - tests/test_grammar.py checks that it is well formed.

Agreement (gender, number, person) is NOT in the productions: it is checked
afterwards by agreement.py (P3). That split is the point of the project: the
CFG describes the structure and the features describe the context, as with
the symbol table in Phase 1.

Notation: non-terminals are phrase labels (O, SN, SV...), terminals are the
lexical categories of tokens.Category (DET, SUST, V...).
"""

from dataclasses import dataclass

from .tokens import Category

START = "O"

# Lexical categories = terminals of the grammar.
TERMINALS = {c.value for c in Category}

# Human-readable names, for docs and for the LLM prompt.
LABELS = {
    "O": "oración",
    "SN": "sintagma nominal",
    "SV": "sintagma verbal",
    "SP": "sintagma preposicional",
    "SA": "sintagma adjetival",
    "SAdv": "sintagma adverbial",
    "DET": "determinante",
    "SUST": "sustantivo",
    "NPROP": "nombre propio",
    "PRON": "pronombre",
    "ADJ": "adjetivo",
    "V": "verbo",
    "ADV": "adverbio",
    "PREP": "preposición",
    "CONJ": "conjunción",
}


@dataclass(frozen=True)
class Production:
    left: str
    right: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.left} → {' '.join(self.right)}"


def P(left: str, right: str) -> Production:
    """Shorthand: P("SN", "DET SUST SA")."""
    return Production(left, tuple(right.split()))


# ----------------------------------------------------------------------
# Productions
# ----------------------------------------------------------------------
# STARTING POINT, to be completed and justified by P1 in docs/gramatica_es.md.
# The assignment asks for: Subject-Verb-Object sentences, adjectives, adverbs,
# prepositional phrases, two verb tenses (features, not productions) and basic
# agreement (features, not productions).
PRODUCTIONS: list[Production] = [
    # Oración: sujeto + predicado
    P("O", "SN SV"),

    # Sintagma nominal
    P("SN", "DET SUST"),
    P("SN", "DET SUST SA"),
    P("SN", "NPROP"),
    P("SN", "PRON"),
    # TODO(P1): ¿SN → DET SA SUST ("la pequeña niña")? ¿SN → DET SUST SP ("el gato de Ana")?
    #           Ojo: SN → DET SUST SP crea ambigüedad con SV → V SN SP.

    # Sintagma adjetival
    P("SA", "ADJ"),
    P("SA", "ADV ADJ"),        # "muy grande"

    # Sintagma verbal
    P("SV", "V"),
    P("SV", "V SN"),
    P("SV", "V SP"),
    P("SV", "V SN SP"),
    P("SV", "V SAdv"),
    P("SV", "V SN SAdv"),
    # TODO(P1): ¿adverbio antes del verbo? ("Ana siempre come")

    # Sintagma adverbial
    P("SAdv", "ADV"),

    # Sintagma preposicional
    P("SP", "PREP SN"),
]


# ----------------------------------------------------------------------
# Helpers (implemented)
# ----------------------------------------------------------------------
def nonterminals() -> list[str]:
    """Non-terminals in order of first appearance (START first)."""
    seen: list[str] = []
    for p in PRODUCTIONS:
        if p.left not in seen:
            seen.append(p.left)
    return seen


def productions_of(left: str) -> list[Production]:
    return [p for p in PRODUCTIONS if p.left == left]


def as_bnf(with_labels: bool = True) -> str:
    """The grammar as text, one line per non-terminal:

        O    ::= SN SV
        SN   ::= DET SUST | DET SUST SA | NPROP | PRON
        ...

    Used in docs and in the LLM prompt (P5).
    """
    names = nonterminals()
    width = max(len(n) for n in names)
    lines = []
    for left in names:
        alternatives = " | ".join(" ".join(p.right) for p in productions_of(left))
        lines.append(f"{left:<{width}} ::= {alternatives}")
    if with_labels:
        used = set(names) | {s for p in PRODUCTIONS for s in p.right}
        shown = [s for s in LABELS if s in used]
        label_width = max(len(s) for s in shown)
        lines.append("")
        lines.append("Categorías:")
        for symbol in shown:
            lines.append(f"  {symbol:<{label_width}} = {LABELS[symbol]}")
    return "\n".join(lines)


def check_grammar() -> list[str]:
    """Problems that make the grammar unusable (empty list = OK).

    - every symbol on the right must be a non-terminal or a terminal;
    - every non-terminal must be reachable from START;
    - no direct left recursion (A → A ...), which a recursive-descent parser
      cannot handle.
    """
    problems = []
    names = set(nonterminals())
    if START not in names:
        problems.append(f"no hay producciones para el símbolo inicial {START}")
    for p in PRODUCTIONS:
        for symbol in p.right:
            if symbol not in names and symbol not in TERMINALS:
                problems.append(f"{p}: el símbolo {symbol} no está definido")
        if p.right and p.right[0] == p.left:
            problems.append(f"{p}: recursión por la izquierda")

    reachable = {START}
    changed = True
    while changed:
        changed = False
        for p in PRODUCTIONS:
            if p.left in reachable:
                for symbol in p.right:
                    if symbol in names and symbol not in reachable:
                        reachable.add(symbol)
                        changed = True
    for name in sorted(names - reachable):
        problems.append(f"{name} no se puede alcanzar desde {START}")
    return problems
