"""Helpers so the parser (P2) and agreement (P3) can be tested before the lexer exists.

    tokens = tokens_from_lexicon("el gato negro come")

Splits on spaces and looks each word up in data/lexicon.json. No error
handling: an unknown word raises, because that is the lexer's job.
"""

from spanish.lexicon import Lexicon
from spanish.tokens import Token

LEXICON = Lexicon.load()


def tokens_from_lexicon(sentence: str) -> list[Token]:
    tokens = []
    column = 1
    for position, word in enumerate(sentence.split(), start=1):
        column = sentence.index(word, column - 1) + 1
        readings = LEXICON.lookup(word)
        if not readings:
            raise ValueError(f"tokens_from_lexicon: '{word}' no está en data/lexicon.json")
        tokens.append(Token(word, position, column, readings))
        column += len(word)
    return tokens
