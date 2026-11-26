"""Recursive-descent parser.  Owner: Person 2.

Implements the grammar of docs/gramatica_es.md, section 1.2 (without left
recursion), exactly as the document says:
  - each non-terminal is a method;
  - each rule `X' → ... X' | ε` (NP', VP') is a `while` loop that repeats
    while the current word can start it;
  - each optional rule (AdjOpc, ObjOpc) is an `if` on the current word.
FIRST sets are in grammar.FIRST.

Input:  the tokens of one sentence (from lexer.py).
Output: (tree, errors)
  - tree:   the Node of the whole sentence (label "S"), or None if rejected.
  - errors: list of ParseError (empty if the sentence was accepted).

Trees are FLATTENED (team decision): NP', AdjOpc, ObjOpc and VP' never
appear; what they contain hangs from the parent. For example:

    Él mató un elefante en sus pijamas.
    (S (NP (NPbase (Prn él)))
       (VP (Verb mató)
           (NP (NPbase (Det un) (Nom (Noun elefante)))
               (PP (Prep en) (NP (NPbase (Pos sus) (Nom (Noun pijamas))))))))

PP ambiguity (document, 1.4): Prep is in FIRST(NP') and in FOLLOW(NP'). The
decision is to attach the PP to the NEAREST noun phrase: the NP' loop keeps
taking PPs while it sees a Prep, so the VP' loop only gets a PP when the verb
has no object ("Ella duerme en la manzana.") or after an Adv.

Agreement is NOT checked here (that is agreement.py): "La elefante grises
duerme." must parse fine and then fail agreement.
"""

from .errors import ParseError
from .grammar import FIRST
from .tokens import CATEGORY_BY_LABEL, Category, Reading, Token
from .tree import Node


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0
        self.errors: list[ParseError] = []

    # ------------------------------------------------------------------
    # Helpers (implemented)
    # ------------------------------------------------------------------
    def at_end(self) -> bool:
        return self.pos >= len(self.tokens)

    def current(self) -> Token | None:
        return None if self.at_end() else self.tokens[self.pos]

    def starts(self, nonterminal: str) -> bool:
        """Can the current word start this non-terminal? (FIRST set check)."""
        token = self.current()
        if token is None:
            return False
        return token.has(*(CATEGORY_BY_LABEL[label] for label in FIRST[nonterminal]))

    def check(self, category: Category) -> bool:
        token = self.current()
        return token is not None and token.has(category)

    def match(self, category: Category) -> Node | None:
        """If the current word can be this category, consume it and return its
        leaf; otherwise return None and consume nothing.

        If the word has several readings of the same category (e.g. two Det
        readings), the first one is taken.
        """
        token = self.current()
        if token is None:
            return None
        readings: list[Reading] = token.readings_of(category)
        if not readings:
            return None
        self.pos += 1
        return Node.leaf(token, readings[0])

    def expect(self, category: Category, what: str) -> Node | None:
        """match(), but report a ParseError if the word is not there.

        `what` is the Spanish name for the message: "un sustantivo", "un verbo"...
        """
        node = self.match(category)
        if node is None:
            token = self.current()
            if token is None:
                self.error(f"la oración terminó, se esperaba {what}")
            else:
                self.error(f"se esperaba {what}", token)
        return node

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
        #   if errors were reported, or words are left over ("no se esperaba 'X'"):
        #       return None, self.errors      (report only the FIRST error)
        #   return tree, []
        #   Hint: an X word (unknown) can only produce a ParseError; make its
        #   message say so: "'que' no está en la gramática".
        raise NotImplementedError("TODO(P2): Parser.parse")

    # ------------------------------------------------------------------
    # One method per non-terminal of grammar.PARSER_PRODUCTIONS
    # ------------------------------------------------------------------
    def sentence(self) -> Node | None:
        """S → NP VP"""
        # TODO(P2)
        raise NotImplementedError("TODO(P2): sentence")

    def noun_phrase(self) -> Node | None:
        """NP → NPbase NP'      NP' → PP NP' | ε     (while loop; flattened: NP → NPbase PP*)"""
        # TODO(P2)
        raise NotImplementedError("TODO(P2): noun_phrase")

    def noun_phrase_base(self) -> Node | None:
        """NPbase → Prn | Det Nom | Pos Nom"""
        # TODO(P2)
        raise NotImplementedError("TODO(P2): noun_phrase_base")

    def nominal(self) -> Node | None:
        """Nom → Noun AdjOpc     AdjOpc → AdjP | ε     (if; flattened: Nom → Noun AdjP?)"""
        # TODO(P2)
        raise NotImplementedError("TODO(P2): nominal")

    def adjective_phrase(self) -> Node | None:
        """AdjP → Adj | Intens Adj"""
        # TODO(P2)
        raise NotImplementedError("TODO(P2): adjective_phrase")

    def verb_phrase(self) -> Node | None:
        """VP → Verb ObjOpc VP'    ObjOpc → NP | ε (if)    VP' → PP VP' | Adv VP' | ε (while)

        Flattened: VP → Verb NP? (PP | Adv)*
        """
        # TODO(P2)
        raise NotImplementedError("TODO(P2): verb_phrase")

    def prepositional_phrase(self) -> Node | None:
        """PP → Prep NP"""
        # TODO(P2)
        raise NotImplementedError("TODO(P2): prepositional_phrase")


def parse(tokens: list[Token]) -> tuple[Node | None, list[ParseError]]:
    """Entry point used by the pipeline and the tests."""
    return Parser(tokens).parse()
