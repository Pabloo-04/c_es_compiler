"""The Spanish CFG as data.  Owner: Person 1.

Executable copy of docs/gramatica_es.md, Part 1. Single source of truth for:
  - parser.py, which implements PARSER_PRODUCTIONS by hand (P2);
  - experiments/prompts.py, which sends the rules to the LLM with as_bnf() (P5);
  - tests/test_grammar_and_data.py, which checks the grammar and the data.

If a rule changes here it must change in the document too (and vice versa),
and the team must be told: the grammar also goes in the LLM prompt.

Two versions, as in the document:
  - REPORT_PRODUCTIONS (section 1.1): readable, with left recursion.
  - PARSER_PRODUCTIONS (section 1.2): without left recursion, for recursive descent.

Agreement (gender, number, person) is NOT in the productions: agreement.py
checks it on the tree (section 1.4).
"""

import re
from dataclasses import dataclass

from .tokens import Category

START = "S"
EPSILON = "ε"

# Lexical categories = terminals of the grammar (X is not: it never derives).
TERMINALS = {c.value for c in Category if c is not Category.X}


@dataclass(frozen=True)
class Production:
    left: str
    right: tuple[str, ...]      # () = ε

    def __str__(self) -> str:
        return f"{self.left} → {' '.join(self.right) or EPSILON}"


def P(left: str, right: str) -> Production:
    """Shorthand: P("NP", "Det Nom"); P("NP'", "ε") for the empty production."""
    symbols = tuple(s for s in right.split() if s != EPSILON)
    return Production(left, symbols)


# ----------------------------------------------------------------------
# Section 1.1: extended grammar (report version). ★ = new, rest from Luque [1].
# ----------------------------------------------------------------------
REPORT_PRODUCTIONS: list[Production] = [
    P("S", "NP VP"),
    P("NP", "Prn"), P("NP", "Det Nom"), P("NP", "Pos Nom"), P("NP", "NP PP"),
    P("Nom", "Noun"), P("Nom", "Noun AdjP"),                    # ★
    P("AdjP", "Adj"), P("AdjP", "Intens Adj"),                  # ★
    P("VP", "Verb NP"), P("VP", "VP PP"),
    P("VP", "Verb"),                                            # ★
    P("VP", "VP Adv"),                                          # ★
    P("PP", "Prep NP"),
]

# ----------------------------------------------------------------------
# Section 1.2: without left recursion (parser version).
# ----------------------------------------------------------------------
PARSER_PRODUCTIONS: list[Production] = [
    P("S", "NP VP"),
    P("NP", "NPbase NP'"),
    P("NPbase", "Prn"), P("NPbase", "Det Nom"), P("NPbase", "Pos Nom"),
    P("NP'", "PP NP'"), P("NP'", "ε"),
    P("Nom", "Noun AdjOpc"),
    P("AdjOpc", "AdjP"), P("AdjOpc", "ε"),
    P("AdjP", "Adj"), P("AdjP", "Intens Adj"),
    P("VP", "Verb ObjOpc VP'"),
    P("ObjOpc", "NP"), P("ObjOpc", "ε"),
    P("VP'", "PP VP'"), P("VP'", "Adv VP'"), P("VP'", "ε"),
    P("PP", "Prep NP"),
]

# Kept for code written against the first version of this module.
PRODUCTIONS = PARSER_PRODUCTIONS

# Auxiliary non-terminals of the parser grammar: they never appear in trees.
AUXILIARY = {"NP'", "AdjOpc", "ObjOpc", "VP'"}

# FIRST sets (document, section 1.2): which categories can start each non-terminal.
FIRST = {
    "S": {"Prn", "Det", "Pos"},
    "NP": {"Prn", "Det", "Pos"},
    "NPbase": {"Prn", "Det", "Pos"},
    "Nom": {"Noun"},
    "AdjP": {"Adj", "Intens"},
    "VP": {"Verb"},
    "PP": {"Prep"},
}

# ----------------------------------------------------------------------
# Flattened tree shapes (team decision, document section 2.4).
# Allowed sequence of child labels for each phrase label, as a regex over
# space-separated labels. The auxiliary nodes are expanded in place:
#   NP  → NPbase NP'        becomes  NP  → NPbase PP*
#   Nom → Noun AdjOpc       becomes  Nom → Noun AdjP?
#   VP  → Verb ObjOpc VP'   becomes  VP  → Verb NP? (PP | Adv)*
# ----------------------------------------------------------------------
TREE_SHAPES: dict[str, str] = {
    "S": r"NP VP",
    "NP": r"NPbase( PP)*",
    "NPbase": r"Prn|Det Nom|Pos Nom",
    "Nom": r"Noun( AdjP)?",
    "AdjP": r"Adj|Intens Adj",
    "VP": r"Verb( NP)?( (PP|Adv))*",
    "PP": r"Prep NP",
}

LABELS = {
    "S": "oración",
    "NP": "sintagma nominal",
    "NPbase": "sintagma nominal sin complementos",
    "Nom": "núcleo nominal (sustantivo y adjetivo)",
    "AdjP": "sintagma adjetival",
    "VP": "sintagma verbal",
    "PP": "sintagma preposicional",
    "Prn": "pronombre",
    "Det": "determinante",
    "Pos": "posesivo",
    "Noun": "sustantivo",
    "Adj": "adjetivo",
    "Intens": "intensificador",
    "Adv": "adverbio",
    "Verb": "verbo",
    "Prep": "preposición",
}


# ----------------------------------------------------------------------
# Helpers (implemented)
# ----------------------------------------------------------------------
def nonterminals(productions: list[Production] = PARSER_PRODUCTIONS) -> list[str]:
    """Non-terminals in order of first appearance (START first)."""
    seen: list[str] = []
    for p in productions:
        if p.left not in seen:
            seen.append(p.left)
    return seen


def as_bnf(productions: list[Production] = PARSER_PRODUCTIONS) -> str:
    """The grammar as text, one line per non-terminal, as in the document:

        S       → NP VP
        NP      → NPbase NP'
        NPbase  → Prn | Det Nom | Pos Nom
        ...

    Used in the LLM prompt (P5) and to compare with the document.
    """
    names = nonterminals(productions)
    width = max(len(n) for n in names) + 1   # same alignment as the document
    lines = []
    for left in names:
        alternatives = " | ".join(
            " ".join(p.right) or EPSILON for p in productions if p.left == left
        )
        lines.append(f"{left:<{width}} → {alternatives}")
    return "\n".join(lines)


def check_grammar(productions: list[Production] = PARSER_PRODUCTIONS, allow_left_recursion: bool = False) -> list[str]:
    """Problems that make the grammar unusable (empty list = OK).

    - every symbol on the right must be a non-terminal or a terminal;
    - every non-terminal must be reachable from START;
    - no direct left recursion (A → A ...), unless allowed (report version).
    """
    problems = []
    names = set(nonterminals(productions))
    if START not in names:
        problems.append(f"no hay producciones para el símbolo inicial {START}")
    for p in productions:
        for symbol in p.right:
            if symbol not in names and symbol not in TERMINALS:
                problems.append(f"{p}: el símbolo {symbol} no está definido")
        if not allow_left_recursion and p.right and p.right[0] == p.left:
            problems.append(f"{p}: recursión por la izquierda")

    reachable = {START}
    changed = True
    while changed:
        changed = False
        for p in productions:
            if p.left in reachable:
                for symbol in p.right:
                    if symbol in names and symbol not in reachable:
                        reachable.add(symbol)
                        changed = True
    for name in sorted(names - reachable):
        problems.append(f"{name} no se puede alcanzar desde {START}")
    return problems


def tree_shape_errors(tree) -> list[str]:
    """Nodes of a tree that do not follow TREE_SHAPES (empty list = valid tree).

    Works with any spanish.tree.Node, including trees parsed from the LLM
    answers, so P4/P5 can measure how many LLM trees respect the grammar.
    """
    problems = []
    if tree.label != START:
        problems.append(f"la raíz es {tree.label}, no {START}")
    for node in tree.walk():
        if node.is_leaf:
            if node.label not in TERMINALS:
                problems.append(f"({node.label} {node.word}): categoría desconocida")
            continue
        shape = TREE_SHAPES.get(node.label)
        children = " ".join(child.label for child in node.children)
        if shape is None:
            problems.append(f"{node.label}: etiqueta de sintagma desconocida")
        elif not re.fullmatch(shape, children):
            problems.append(f"{node.label} → {children}: no está permitido")
    return problems
