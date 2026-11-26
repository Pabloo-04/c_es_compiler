"""Shared contracts: Token, Node and diagnostics. These pass from day 1."""

import pytest

from spanish.errors import AgreementError, LexicalError, ParseError, sort_by_position
from spanish.grammar import tree_shape_errors
from spanish.tokens import Category, Features, Reading, Token
from spanish.tree import Node, same_tree

# Example of docs/gramatica_es.md, section 2.4.
TREE = "(S (NP (NPbase (Prn ella))) (VP (Verb come) (NP (NPbase (Det una) (Nom (Noun manzana))))))"


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------
def test_categories_are_the_agreed_ones():
    assert [c.value for c in Category] == ["Prn", "Det", "Pos", "Noun", "Adj", "Intens", "Adv", "Verb", "Prep", "X"]


def test_features_reject_invalid_values():
    with pytest.raises(ValueError):
        Features(gender="masc")
    with pytest.raises(ValueError):
        Features(tense="presente")


def test_reading_str():
    r = Reading(Category.NOUN, "niña", Features(gender="f", number="sg"))
    assert str(r) == "Noun(niña, f, sg)"


def test_ambiguous_and_unknown_tokens():
    adj = Reading(Category.ADJ, "bajo", Features("m", "sg"))
    prep = Reading(Category.PREP, "bajo")
    token = Token("bajo", 1, 1, (adj, prep))
    assert token.is_ambiguous and token.has(Category.PREP) and not token.has(Category.VERB)
    assert Token("que", 1, 1, (Reading(Category.X, "que"),)).is_unknown


# ---------------------------------------------------------------------------
# Tree
# ---------------------------------------------------------------------------
def test_bracketed_round_trip():
    assert Node.from_bracketed(TREE).to_bracketed() == TREE


def test_bracketed_ignores_whitespace_and_word_case():
    messy = "(S\n  (NP (NPbase (Prn Ella)))\n  (VP (Verb come) (NP (NPbase (Det una) (Nom (Noun manzana))))))"
    assert same_tree(messy, TREE)
    assert not same_tree(TREE.replace("Prn", "PRN"), TREE)


@pytest.mark.parametrize("bad", ["", "(S", "(S (NP (NPbase (Prn ella)))", "S (NP)", "(S) (VP)", "(S (NP (Prn x))) extra"])
def test_malformed_trees_raise(bad):
    with pytest.raises(ValueError):
        Node.from_bracketed(bad)


def test_leaves_and_navigation():
    tree = Node.from_bracketed(TREE)
    assert [(leaf.label, leaf.word) for leaf in tree.leaves()] == [
        ("Prn", "ella"), ("Verb", "come"), ("Det", "una"), ("Noun", "manzana"),
    ]
    assert len(tree.find_all("NPbase")) == 2
    assert tree.child("VP").child("Verb").word == "come"


def test_same_tree_with_none():
    assert same_tree(None, None)
    assert not same_tree(TREE, None)


# ---------------------------------------------------------------------------
# Flattened tree shapes (grammar.TREE_SHAPES)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("tree", [
    TREE,
    "(S (NP (NPbase (Prn él))) (VP (Verb mató) (NP (NPbase (Det un) (Nom (Noun elefante))) "
    "(PP (Prep en) (NP (NPbase (Pos sus) (Nom (Noun pijamas))))))))",
    "(S (NP (NPbase (Det los) (Nom (Noun perros) (AdjP (Intens muy) (Adj grandes))))) "
    "(VP (Verb durmieron) (Adv ayer)))",
])
def test_valid_tree_shapes(tree):
    assert tree_shape_errors(Node.from_bracketed(tree)) == []


@pytest.mark.parametrize("tree", [
    "(O (NP (NPbase (Prn ella))) (VP (Verb come)))",                         # wrong root
    "(S (NP (NPbase (Prn ella)) (NP' (PP (Prep en) (NP (NPbase (Prn él)))))) (VP (Verb come)))",  # auxiliary node
    "(S (NP (NPbase (Det la) (Noun niña))) (VP (Verb come)))",               # Noun without Nom
    "(S (NP (NPbase (DET la) (Nom (Noun niña)))) (VP (Verb come)))",         # unknown category
])
def test_invalid_tree_shapes(tree):
    assert tree_shape_errors(Node.from_bracketed(tree)) != []


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------
def test_single_format():
    e = AgreementError(2, "elefante", "el determinante 'la' no concuerda en género con 'elefante'")
    assert str(e) == "Palabra 2 ('elefante'): el determinante 'la' no concuerda en género con 'elefante'"
    assert str(ParseError(None, None, "falta el verbo")) == "Oración: falta el verbo"


def test_error_types_are_the_two_agreed_values():
    assert {LexicalError.error_type, ParseError.error_type, AgreementError.error_type} == {"sintactico", "concordancia"}


def test_sort_by_position_puts_sentence_errors_first():
    a, b, c = LexicalError(3, "x", "m"), ParseError(None, None, "m"), LexicalError(1, "y", "m")
    assert sort_by_position([a, b, c]) == [b, c, a]


def test_bracketed_lowercase_for_the_results_files():
    assert Node.from_bracketed("(S (NP (NPbase (Prn Ella))) (VP (Verb come)))").to_bracketed(lowercase=True) == (
        "(S (NP (NPbase (Prn ella))) (VP (Verb come)))"
    )
