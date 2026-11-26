"""Helpers so the parser (P2) and agreement (P3) can be tested before the lexer exists.

    tokens = tokens_from_lexicon("Ella come una manzana.")
    tree = tree_from_lexicon("(S (NP (NPbase (Prn ella))) (VP (Verb come)))")

Words are looked up in data/lexicon.json; unknown words get category X, as
the real lexer does.
"""

from spanish.lexicon import Lexicon
from spanish.tokens import Category, Reading, Token
from spanish.tree import Node

LEXICON = Lexicon.load()


def tokens_from_lexicon(sentence: str) -> list[Token]:
    text = sentence.rstrip().rstrip(".")
    tokens = []
    column = 1
    for position, word in enumerate(text.split(), start=1):
        column = text.index(word, column - 1) + 1
        readings = LEXICON.lookup(word) or (Reading(Category.X, word.lower()),)
        tokens.append(Token(word, position, column, readings))
        column += len(word)
    return tokens


def tree_from_lexicon(bracketed: str) -> Node:
    """Bracketed tree -> Node whose leaves carry the lexicon reading of that category."""
    tree = Node.from_bracketed(bracketed)
    for position, leaf in enumerate(tree.leaves(), start=1):
        readings = LEXICON.lookup(leaf.word)
        leaf.token = Token(leaf.word, position, 1, readings)
        leaf.reading = next(r for r in readings if r.category.value == leaf.label)
    return tree
