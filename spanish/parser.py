"""Recursive-descent parser for the Spanish grammar.

Input: tokens for one sentence.
Output: (tree, []) on success, or (None, [error]) on failure.
"""

from .errors import ParseError
from .grammar import productions_of
from .tokens import Category, Token
from .tree import Node


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.furthest = 0

        # Each non-terminal has a corresponding parser method.
        self.phrases = {
            "O": self.sentence,
            "SN": self.noun_phrase,
            "SV": self.verb_phrase,
            "SA": self.adjective_phrase,
            "SAdv": self.adverb_phrase,
            "SP": self.prepositional_phrase,
        }

    def parse(self) -> tuple[Node | None, list[ParseError]]:
        """Return the first sentence tree that consumes every token."""
        for tree, end in self.sentence(0):
            if end == len(self.tokens):
                return tree, []

        if self.furthest == len(self.tokens):
            error = ParseError(None, None, "Oración incompleta.")
        else:
            token = self.tokens[self.furthest]
            error = ParseError(
                token.position,
                token.word,
                f"No se esperaba '{token.word}' en esta posición.",
            )

        return None, [error]

    # One entry point per non-terminal in grammar.py.

    def sentence(self, pos: int):
        """O: oración."""
        yield from self.phrase("O", pos)

    def noun_phrase(self, pos: int):
        """SN: sintagma nominal."""
        yield from self.phrase("SN", pos)

    def verb_phrase(self, pos: int):
        """SV: sintagma verbal."""
        yield from self.phrase("SV", pos)

    def adjective_phrase(self, pos: int):
        """SA: sintagma adjetival."""
        yield from self.phrase("SA", pos)

    def adverb_phrase(self, pos: int):
        """SAdv: sintagma adverbial."""
        yield from self.phrase("SAdv", pos)

    def prepositional_phrase(self, pos: int):
        """SP: sintagma preposicional."""
        yield from self.phrase("SP", pos)

    def phrase(self, label: str, pos: int):
        """Try each production for this non-terminal from the same position."""
        for production in productions_of(label):
            for children, end in self.sequence(production.right, pos):
                yield Node(label, children), end

    def sequence(self, symbols: tuple[str, ...], pos: int):
        """Recognize all symbols on the right-hand side, from left to right."""
        if not symbols:
            yield [], pos
            return

        first_symbol = symbols[0]
        remaining_symbols = symbols[1:]

        for first_node, next_pos in self.symbol(first_symbol, pos):
            for other_nodes, end in self.sequence(remaining_symbols, next_pos):
                yield [first_node, *other_nodes], end

    def symbol(self, name: str, pos: int):
        """Expand a non-terminal or match a lexical category."""
        if name in self.phrases:
            yield from self.phrases[name](pos)
            return

        if pos >= len(self.tokens):
            return

        token = self.tokens[pos]
        category = Category(name)

        for reading in token.readings_of(category):
            next_pos = pos + 1
            self.furthest = max(self.furthest, next_pos)
            yield Node.leaf(token, reading), next_pos


def parse(tokens: list[Token]) -> tuple[Node | None, list[ParseError]]:
    """Entry point used by the pipeline and the tests."""
    return Parser(tokens).parse()