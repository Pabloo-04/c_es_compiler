"""Recursive-descent parser for the Spanish grammar S -> NP VP.

Each phrase method consumes its tokens and builds a node of the syntax tree.
Optional phrases use FIRST sets. Repeated modifiers are attached directly
to their parent, following the tree format agreed by the team.
"""

from .errors import ParseError
from .grammar import FIRST
from .tokens import CATEGORY_BY_LABEL, Category, Token
from .tree import Node


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0
        self.errors: list[ParseError] = []

    def current(self) -> Token | None:
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]

    def starts(self, nonterminal: str) -> bool:
        """Check whether the current token can start this phrase."""
        token = self.current()
        if token is None:
            return False
        categories = [CATEGORY_BY_LABEL[label] for label in FIRST[nonterminal]]
        return token.has(*categories)

    def check(self, category: Category) -> bool:
        token = self.current()
        return token is not None and token.has(category)

    def match(self, category: Category) -> Node | None:
        """Consume one token if it has a reading of the requested category."""
        token = self.current()
        if token is None:
            return None

        readings = token.readings_of(category)
        if not readings:
            return None

        self.pos += 1
        return Node.leaf(token, readings[0])

    def error(self, message: str) -> None:
        token = self.current()
        if token is None:
            self.errors.append(ParseError(None, None, message))
            return

        if token.has(Category.X):
            message = f"'{token.word}' no está en la gramática."
        self.errors.append(ParseError(token.position, token.word, message))

    def expect(self, category: Category, description: str) -> Node | None:
        """Consume a required category or record the reason for rejection."""
        node = self.match(category)
        if node is None:
            if self.current() is None:
                self.error(f"La oración terminó, se esperaba {description}.")
            else:
                self.error(f"Se esperaba {description}.")
        return node

    def parse(self) -> tuple[Node | None, list[ParseError]]:
        """Accept only when the sentence consumes all tokens."""
        tree = self.sentence()
        if self.errors:
            return None, self.errors[:1]

        token = self.current()
        if token is not None:
            self.error(f"No se esperaba '{token.word}'.")
            return None, self.errors

        return tree, []

    def sentence(self) -> Node | None:
        """S -> NP VP."""
        subject = self.noun_phrase()
        if subject is None:
            return None

        predicate = self.verb_phrase()
        if predicate is None:
            return None

        return Node("S", [subject, predicate])

    def noun_phrase(self) -> Node | None:
        """NP -> NPbase PP*. Attach each PP to the nearest noun phrase."""
        base = self.noun_phrase_base()
        if base is None:
            return None

        children = [base]
        while self.starts("PP"):
            modifier = self.prepositional_phrase()
            if modifier is None:
                return None
            children.append(modifier)

        return Node("NP", children)

    def noun_phrase_base(self) -> Node | None:
        """NPbase -> Prn | Det Nom | Pos Nom."""
        pronoun = self.match(Category.PRN)
        if pronoun is not None:
            return Node("NPbase", [pronoun])

        determiner = self.match(Category.DET) or self.match(Category.POS)
        if determiner is None:
            self.error("Se esperaba un pronombre, determinante o posesivo.")
            return None

        nominal = self.nominal()
        if nominal is None:
            return None

        return Node("NPbase", [determiner, nominal])

    def nominal(self) -> Node | None:
        """Nom -> Noun AdjP?."""
        noun = self.expect(Category.NOUN, "un sustantivo")
        if noun is None:
            return None

        children = [noun]
        if self.starts("AdjP"):
            adjective = self.adjective_phrase()
            if adjective is None:
                return None
            children.append(adjective)

        return Node("Nom", children)

    def adjective_phrase(self) -> Node | None:
        """AdjP -> Adj | Intens Adj."""
        intensifier = self.match(Category.INTENS)
        adjective = self.expect(Category.ADJ, "un adjetivo")
        if adjective is None:
            return None

        if intensifier is None:
            return Node("AdjP", [adjective])
        return Node("AdjP", [intensifier, adjective])

    def verb_phrase(self) -> Node | None:
        """VP -> Verb NP? (PP | Adv)*."""
        verb = self.expect(Category.VERB, "un verbo")
        if verb is None:
            return None

        children = [verb]
        if self.starts("NP"):
            obj = self.noun_phrase()
            if obj is None:
                return None
            children.append(obj)

        while self.starts("PP") or self.check(Category.ADV):
            if self.starts("PP"):
                modifier = self.prepositional_phrase()
            else:
                modifier = self.match(Category.ADV)

            if modifier is None:
                return None
            children.append(modifier)

        return Node("VP", children)

    def prepositional_phrase(self) -> Node | None:
        """PP -> Prep NP."""
        preposition = self.expect(Category.PREP, "una preposición")
        if preposition is None:
            return None

        complement = self.noun_phrase()
        if complement is None:
            return None

        return Node("PP", [preposition, complement])


def parse(tokens: list[Token]) -> tuple[Node | None, list[ParseError]]:
    """Entry point used by the pipeline and the tests."""
    return Parser(tokens).parse()