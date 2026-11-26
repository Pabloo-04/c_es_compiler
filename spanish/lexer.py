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

import unicodedata

from .errors import LexicalError
from .lexicon import Lexicon
from .tokens import Category, Reading, Token

# The agreed test sentences end with a single period (docs/gramatica_es.md 2.3).
FINAL_PUNCTUATION = ".!?"


# Spanish alphabet: the 26 Latin letters plus ñ and the accented vowels (and ü).
# str.isalpha() would also accept letters of any other alphabet (я, 字, ç...),
# which are not Spanish, so they are reported as invalid characters instead.
SPANISH_LETTERS = frozenset("abcdefghijklmnopqrstuvwxyzáéíóúüñABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ")


def is_letter(c: str) -> bool:
    return c in SPANISH_LETTERS


def unknown_reading(word: str) -> Reading:
    return Reading(Category.X, word.lower())


class Lexer:
    def __init__(self, sentence: str, lexicon: Lexicon) -> None:
        self.sentence = sentence
        self.lexicon = lexicon
        self.tokens: list[Token] = []
        self.errors: list[LexicalError] = []

    def analyze(self) -> tuple[list[Token], list[LexicalError]]:
        # Text typed on some systems stores "é" as "e" + a combining accent
        # (NFD). Normalize to NFC so each accented letter is ONE character.
        text = unicodedata.normalize("NFC", self.sentence).rstrip()
        self.tokens, self.errors = [], []

        # A single final punctuation mark is ignored; anywhere else it is invalid.
        end = len(text) - 1 if text and text[-1] in FINAL_PUNCTUATION else len(text)

        i = 0
        while i < end:
            c = text[i]
            if c.isspace():
                i += 1
            elif is_letter(c):
                start = i
                while i < end and is_letter(text[i]):
                    i += 1
                self.add_word(text[start:i], column=start + 1)
            else:
                self.errors.append(
                    LexicalError(None, c, f"carácter inválido '{c}' (columna {i + 1})")
                )
                i += 1
        return self.tokens, self.errors

    def add_word(self, word: str, column: int) -> None:
        """Create the token of a word: its readings come from the lexicon."""
        readings = self.lexicon.lookup(word) or (unknown_reading(word),)
        self.tokens.append(Token(word, len(self.tokens) + 1, column, readings))


def tokenize(sentence: str, lexicon: Lexicon | None = None) -> tuple[list[Token], list[LexicalError]]:
    """Entry point used by the pipeline and the tests."""
    return Lexer(sentence, lexicon or Lexicon.load()).analyze()
