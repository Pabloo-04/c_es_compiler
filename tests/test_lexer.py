"""Lexer tests.  Owner: Person 5 (with P3). Fail with NotImplementedError until lexer.py is done."""

from spanish.lexer import tokenize
from spanish.tokens import Category


def test_words_positions_and_columns():
    tokens, errors = tokenize("el gato  come")
    assert errors == []
    assert [(t.word, t.position, t.column) for t in tokens] == [("el", 1, 1), ("gato", 2, 4), ("come", 3, 10)]


def test_readings_come_from_the_lexicon():
    tokens, _ = tokenize("gatos")
    reading = tokens[0].readings[0]
    assert (reading.category, reading.features.gender, reading.features.number) == (Category.NOUN, "masc", "pl")


def test_capital_letter_and_final_period():
    tokens, errors = tokenize("El gato come.")
    assert errors == []
    assert [t.word for t in tokens] == ["El", "gato", "come"]


def test_accented_words():
    tokens, errors = tokenize("la niña pequeña")
    assert errors == []
    assert tokens[1].word == "niña"


def test_unknown_word_is_reported_and_keeps_positions():
    tokens, errors = tokenize("el dragón come")
    assert len(errors) == 1
    assert errors[0].position == 2 and errors[0].word == "dragón"
    assert [t.position for t in tokens] == [1, 2, 3]


def test_invalid_character():
    _, errors = tokenize("el gato # come")
    assert len(errors) == 1
    assert "#" in errors[0].message


def test_ambiguous_word_keeps_all_readings():
    tokens, _ = tokenize("bajo")
    assert tokens[0].is_ambiguous


# TODO(P5): comma inside the sentence? several spaces/tabs? "¿" and "¡" at the start?
