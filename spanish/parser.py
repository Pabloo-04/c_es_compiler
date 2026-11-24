"""Recursive-descent parser.  Owner: Person 2.

Input:  the tokens of one sentence (from lexer.py).
Output: (tree, errors)
  - tree:   the Node of the whole sentence (label "O"), or None if rejected.
  - errors: list of ParseError (empty if the sentence was accepted).

One method per non-terminal of spanish/grammar.py, exactly like the
ExpressionChecker of Phase 1 (fase1/compiler/type_rules.py), which had one
method per precedence level.

The difference with Phase 1: words can be ambiguous and some non-terminals
have alternatives that start with the same symbol (SV → V | V SN | V SN SP),
so the parser needs BACKTRACKING: remember the position, try an alternative,
and go back if it fails. mark()/reset() are implemented for that.

Agreement is NOT checked here (that is agreement.py): "el gatos come" must
parse fine and then fail agreement. Keeping them apart lets the metrics tell
a syntax error from an agreement error.
"""

from .errors import ParseError
from .tokens import Category, Reading, Token
from .tree import Node


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0
        self.errors: list[ParseError] = []
        # Furthest position reached: the best place to report "unexpected word".
        self.furthest = 0

    # ------------------------------------------------------------------
    # Helpers (implemented)
    # ------------------------------------------------------------------
    def at_end(self) -> bool:
        return self.pos >= len(self.tokens)

    def current(self) -> Token | None:
        return None if self.at_end() else self.tokens[self.pos]

    def mark(self) -> int:
        """Save the position before trying an alternative."""
        return self.pos

    def reset(self, mark: int) -> None:
        """Go back to a saved position (backtracking)."""
        self.pos = mark

    def match(self, category: Category) -> Node | None:
        """If the current word has a reading of this category, consume it and
        return its leaf; otherwise return None and consume nothing.

        If the word has several readings of the same category (e.g. two DET
        readings with different gender), the first one is taken.
        TODO(P2): decide whether that is enough or whether to try them all.
        """
        token = self.current()
        if token is None:
            return None
        readings: list[Reading] = token.readings_of(category)
        if not readings:
            return None
        self.pos += 1
        self.furthest = max(self.furthest, self.pos)
        return Node.leaf(token, readings[0])

    def error(self, message: str, token: Token | None = None) -> None:
        if token is None:
            self.errors.append(ParseError(None, None, message))
        else:
            self.errors.append(ParseError(token.position, token.word, message))

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def parse(self) -> tuple[Node | None, list[ParseError]]:
        # TODO(P2):
        #   tree = self.sentence()
        #   if tree is None or not self.at_end():
        #       report ONE error, pointing at self.tokens[self.furthest] if it
        #       exists ("no se esperaba 'X' aquí"), or "oración incompleta".
        #       return None, self.errors
        #   return tree, []
        raise NotImplementedError("TODO(P2): Parser.parse")

    # ------------------------------------------------------------------
    # One method per non-terminal (keep in sync with grammar.PRODUCTIONS)
    # ------------------------------------------------------------------
    def sentence(self) -> Node | None:
        """O → SN SV"""
        # TODO(P2)
        raise NotImplementedError("TODO(P2): sentence")

    def noun_phrase(self) -> Node | None:
        """SN → DET SUST | DET SUST SA | NPROP | PRON"""
        # TODO(P2): try the longest alternative first (DET SUST SA before DET SUST).
        raise NotImplementedError("TODO(P2): noun_phrase")

    def verb_phrase(self) -> Node | None:
        """SV → V | V SN | V SP | V SN SP | V SAdv | V SN SAdv"""
        # TODO(P2): longest first + backtracking with mark()/reset().
        raise NotImplementedError("TODO(P2): verb_phrase")

    def adjective_phrase(self) -> Node | None:
        """SA → ADJ | ADV ADJ"""
        # TODO(P2)
        raise NotImplementedError("TODO(P2): adjective_phrase")

    def adverb_phrase(self) -> Node | None:
        """SAdv → ADV"""
        # TODO(P2)
        raise NotImplementedError("TODO(P2): adverb_phrase")

    def prepositional_phrase(self) -> Node | None:
        """SP → PREP SN"""
        # TODO(P2)
        raise NotImplementedError("TODO(P2): prepositional_phrase")


def parse(tokens: list[Token]) -> tuple[Node | None, list[ParseError]]:
    """Entry point used by the pipeline and the tests."""
    return Parser(tokens).parse()
