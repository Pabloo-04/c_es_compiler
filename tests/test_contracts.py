"""Shared contracts: Token, Node and diagnostics. These pass from day 1."""

import pytest

from spanish.errors import AgreementError, LexicalError, ParseError, sort_by_position
from spanish.tokens import Category, Features, Reading, Token
from spanish.tree import Node, same_tree

TREE = "(O (SN (DET el) (SUST gato) (SA (ADJ negro))) (SV (V come)))"


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------
def test_features_reject_invalid_values():
    with pytest.raises(ValueError):
        Features(gender="neutro")
    with pytest.raises(ValueError):
        Features(number="dual")


def test_reading_str():
    r = Reading(Category.NOUN, "gato", Features(gender="masc", number="sg"))
    assert str(r) == "SUST(gato, masc, sg)"


def test_ambiguous_token():
    adj = Reading(Category.ADJ, "bajo", Features("masc", "sg"))
    prep = Reading(Category.PREP, "bajo")
    token = Token("bajo", 1, 1, (adj, prep))
    assert token.is_ambiguous
    assert token.readings_of(Category.PREP) == [prep]
    assert token.readings_of(Category.VERB) == []


# ---------------------------------------------------------------------------
# Tree
# ---------------------------------------------------------------------------
def test_bracketed_round_trip():
    assert Node.from_bracketed(TREE).to_bracketed() == TREE


def test_bracketed_ignores_whitespace():
    messy = "(O\n  (SN (DET el)   (SUST gato) (SA (ADJ negro)))\n  (SV (V come)))"
    assert same_tree(messy, TREE)


@pytest.mark.parametrize("bad", ["", "(O", "(O (SN (DET el))", "O (SN)", "(O) (SV)", "(O (SN (DET el)) extra"])
def test_malformed_trees_raise(bad):
    with pytest.raises(ValueError):
        Node.from_bracketed(bad)


def test_leaves_and_find_all():
    tree = Node.from_bracketed(TREE)
    assert [leaf.word for leaf in tree.leaves()] == ["el", "gato", "negro", "come"]
    assert [leaf.label for leaf in tree.leaves()] == ["DET", "SUST", "ADJ", "V"]
    assert len(tree.find_all("SN")) == 1
    assert tree.child("SV").children[0].word == "come"


def test_leaf_from_token_keeps_the_reading():
    reading = Reading(Category.NOUN, "gato", Features("masc", "sg"))
    token = Token("Gato", 2, 4, (reading,))
    leaf = Node.leaf(token, reading)
    assert (leaf.label, leaf.word, leaf.reading) == ("SUST", "Gato", reading)


def test_same_tree_ignores_word_case_but_not_labels():
    assert same_tree("(O (SN (PRON Ella)) (SV (V come)))", "(O (SN (PRON ella)) (SV (V come)))")
    assert not same_tree("(O (SN (PRON ella)) (SV (V come)))", "(O (SN (pron ella)) (SV (V come)))")


def test_same_tree_with_none():
    assert same_tree(None, None)
    assert not same_tree(TREE, None)


def test_pretty():
    assert Node.from_bracketed("(O (SN (PRON ella)) (SV (V come)))").pretty() == (
        "O\n  SN\n    PRON ella\n  SV\n    V come"
    )


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------
def test_single_format():
    e = AgreementError(2, "gatos", "el determinante 'el' no concuerda en número con 'gatos'")
    assert str(e) == "Palabra 2 ('gatos'): el determinante 'el' no concuerda en número con 'gatos'"
    assert str(ParseError(None, None, "falta el verbo")) == "Oración: falta el verbo"


def test_error_types_match_the_results_format():
    assert LexicalError.error_type == "lexico"
    assert ParseError.error_type == "sintactico"
    assert AgreementError.error_type == "concordancia"


def test_sort_by_position_puts_sentence_errors_first():
    a, b, c = LexicalError(3, "x", "m"), ParseError(None, None, "m"), LexicalError(1, "y", "m")
    assert sort_by_position([a, b, c]) == [b, c, a]
