"""Lexer for Spanish sentences.  Owner: Person 3 (adapted from fase1/compiler/lexer.py).

Input:  one sentence as text, e.g. "Ella come una manzana."
Output: (tokens, errors)
  - tokens: list of Token (word, position, column, readings from the lexicon).
  - errors: list of LexicalError (only for characters that cannot be part of a word).

Same rule as Phase 1: report and keep going, never raise.

Differences with Phase 1:
  - The alphabet now includes á é í ó ú ü ñ and their uppercase forms.
  - There are no numbers or operators: a token is a word.
  - The category does not come from the shape of the word (regex) but from the
    lexicon: the same shape can be Noun, Verb or Adj.
  - A word that is NOT in the lexicon is not an error here: it gets one reading
    of category X ("outside the grammar", docs/gramatica_es.md 2.2) and the
    parser rejects the sentence as "sintactico". That way the parser output
    still has its tags (the word is tagged X).
"""

from .errors import LexicalError
from .lexicon import Lexicon
from .tokens import Category, Reading, Token

# The agreed test sentences end with a single period (docs/gramatica_es.md 2.3).
FINAL_PUNCTUATION = ".!?"


def is_letter(c: str) -> bool:
    # str.isalpha() accepts á, ñ, ü... and also letters from any alphabet.
    # TODO(P3): restrict to the Spanish alphabet if the team prefers it.
    return len(c) == 1 and c.isalpha()


def unknown_reading(word: str) -> Reading:
    return Reading(Category.X, word.lower())


class Lexer:
    def __init__(self, sentence: str, lexicon: Lexicon) -> None:
        self.sentence = sentence
        self.lexicon = lexicon
        self.tokens: list[Token] = []
        self.errors: list[LexicalError] = []

    def analyze(self) -> tuple[list[Token], list[LexicalError]]:
        # TODO(P3):
        #   1. Walk the sentence character by character keeping the column (1-based).
        #   2. Spaces separate words.
        #   3. A run of letters is a word: position = 1, 2, 3...
        #      readings = self.lexicon.lookup(word) or (unknown_reading(word),)
        #   4. Final punctuation (FINAL_PUNCTUATION) at the end: ignore it.
        #   5. Any other character -> LexicalError(None, c, f"carácter inválido '{c}'")
        #      and keep going.
        raise NotImplementedError("TODO(P3): Lexer.analyze")


def tokenize(sentence: str, lexicon: Lexicon | None = None) -> tuple[list[Token], list[LexicalError]]:
    """Entry point used by the pipeline and the tests."""
    return Lexer(sentence, lexicon or Lexicon.load()).analyze()
