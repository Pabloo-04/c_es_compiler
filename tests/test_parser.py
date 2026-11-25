"""Parser tests.  Owner: Person 5 (with P2). Fail with NotImplementedError until parser.py is done.

They use tokens_from_lexicon(), so they do not depend on the lexer.
"""

import pytest

from helpers import tokens_from_lexicon
from spanish.parser import parse
from spanish.tree import same_tree


def tree_of(sentence: str):
    tree, errors = parse(tokens_from_lexicon(sentence))
    return tree, errors


@pytest.mark.parametrize("sentence, expected", [
    ("el gato come", "(O (SN (DET el) (SUST gato)) (SV (V come)))"),
    ("ella come", "(O (SN (PRON ella)) (SV (V come)))"),
    ("ana lee un libro", "(O (SN (NPROP ana)) (SV (V lee) (SN (DET un) (SUST libro))))"),
    ("el perro negro corre", "(O (SN (DET el) (SUST perro) (SA (ADJ negro))) (SV (V corre)))"),
    ("el gato come en la casa", "(O (SN (DET el) (SUST gato)) (SV (V come) (SP (PREP en) (SN (DET la) (SUST casa)))))"),
    ("el perro corre rápidamente", "(O (SN (DET el) (SUST perro)) (SV (V corre) (SAdv (ADV rápidamente))))"),
])
def test_accepts_and_builds_the_tree(sentence, expected):
    tree, errors = tree_of(sentence)
    assert errors == []
    assert same_tree(tree, expected)


@pytest.mark.parametrize("sentence", ["come el gato", "el gato", "el come", "gato el come"])
def test_rejects_structures_outside_the_grammar(sentence):
    tree, errors = tree_of(sentence)
    assert tree is None
    assert len(errors) == 1
    assert errors[0].error_type == "sintactico"


def test_agreement_is_not_the_parsers_job():
    # "el gatos come" has a valid STRUCTURE; agreement.py rejects it later.
    tree, errors = tree_of("el gatos come")
    assert tree is not None and errors == []


def test_ambiguous_word_is_resolved_by_the_grammar():
    # "bajo" is ADJ or PREP; here only PREP fits.
    tree, errors = tree_of("el gato come bajo la casa")
    assert errors == []
    assert tree.find_all("SP")[0].children[0].label == "PREP"


# TODO(P5): error position: "el gato come la" -> error at "la" / "oración incompleta".
