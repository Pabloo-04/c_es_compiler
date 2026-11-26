"""Lexer tests.  Owner: Person 5 (with P3). Fail with NotImplementedError until lexer.py is done."""

from spanish.lexer import tokenize
from spanish.tokens import Category


def test_words_positions_and_columns():
    tokens, errors = tokenize("Ella  come una manzana.")
    assert errors == []
    assert [(t.word, t.position, t.column) for t in tokens] == [
        ("Ella", 1, 1), ("come", 2, 7), ("una", 3, 12), ("manzana", 4, 16),
    ]


def test_readings_come_from_the_lexicon():
    tokens, _ = tokenize("perros")
    reading = tokens[0].readings[0]
    assert (reading.category, reading.features.gender, reading.features.number) == (Category.NOUN, "m", "pl")


def test_accented_words():
    tokens, errors = tokenize("Él mató un elefante.")
    assert errors == []
    assert [t.word for t in tokens] == ["Él", "mató", "un", "elefante"]
    assert tokens[0].readings[0].category is Category.PRN


def test_unknown_word_is_tagged_x_not_an_error():
    tokens, errors = tokenize("La manzana roja que comió ella.")
    assert errors == []
    assert tokens[3].is_unknown and tokens[3].readings[0].category is Category.X


def test_invalid_character_is_a_lexical_error():
    _, errors = tokenize("Ella come # una manzana.")
    assert len(errors) == 1
    assert "#" in errors[0].message


def test_ambiguous_word_keeps_all_readings():
    tokens, _ = tokenize("bajo")
    assert tokens[0].is_ambiguous
