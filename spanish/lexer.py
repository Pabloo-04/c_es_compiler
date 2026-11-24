"""Lexer for Spanish sentences.  Owner: Person 3 (adapted from fase1/compiler/lexer.py).

Input:  one sentence as text, e.g. "El gato negro come pescado."
Output: (tokens, errors)
  - tokens: list of Token (word, position, column, readings from the lexicon).
  - errors: list of LexicalError (unknown words, invalid characters).

Same rules as Phase 1: report and keep going, never raise.

Differences with Phase 1:
  - The alphabet now includes á é í ó ú ü ñ and their uppercase forms.
  - There are no numbers or operators: a token is a word.
  - The category does not come from the shape of the word (regex) but from the
    lexicon: the same shape [a-záéíóúüñ]+ can be SUST, V or ADJ.
"""

from .errors import LexicalError
from .lexicon import Lexicon
from .tokens import Token

# Final punctuation allowed (and ignored) at the end of the sentence.
FINAL_PUNCTUATION = ".!?"


def is_letter(c: str) -> bool:
    # str.isalpha() accepts á, ñ, ü... and also letters from any alphabet.
    # TODO(P3): restrict to the Spanish alphabet if the team prefers it.
    return len(c) == 1 and c.isalpha()


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
        #      readings = self.lexicon.lookup(word)
        #      no readings -> LexicalError(position, word, "palabra desconocida")
        #      (still add the Token with readings=() so positions do not shift).
        #   4. Final punctuation (FINAL_PUNCTUATION) at the end: ignore it.
        #   5. Any other character -> LexicalError(None or position, char,
        #      f"carácter inválido '{c}'") and keep going.
        # TODO(P3): mayúscula inicial ("El") -> lookup ya es insensible a mayúsculas,
        #           pero ¿se acepta "eL"? ¿y nombres propios que no están en el léxico?
        raise NotImplementedError("TODO(P3): Lexer.analyze")


def tokenize(sentence: str, lexicon: Lexicon | None = None) -> tuple[list[Token], list[LexicalError]]:
    """Entry point used by the pipeline and the tests."""
    return Lexer(sentence, lexicon or Lexicon.load()).analyze()
