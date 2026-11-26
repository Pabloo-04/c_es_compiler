"""Parser tests.  Owner: Person 5 (with P2). Fail with NotImplementedError until parser.py is done.

They use tokens_from_lexicon(), so they do not depend on the lexer. Expected
trees are flattened (no NP', AdjOpc, ObjOpc or VP').
"""

import pytest

from helpers import tokens_from_lexicon
from spanish.grammar import tree_shape_errors
from spanish.parser import parse
from spanish.tree import same_tree


def tree_of(sentence: str):
    return parse(tokens_from_lexicon(sentence))


@pytest.mark.parametrize("sentence, expected", [
    # Example of docs/gramatica_es.md, 2.4.
    ("Ella come una manzana.",
     "(S (NP (NPbase (Prn ella))) (VP (Verb come) (NP (NPbase (Det una) (Nom (Noun manzana))))))"),
    ("Los perros grandes durmieron.",
     "(S (NP (NPbase (Det los) (Nom (Noun perros) (AdjP (Adj grandes))))) (VP (Verb durmieron)))"),
    ("Él mató un elefante muy gris ayer.",
     "(S (NP (NPbase (Prn él))) (VP (Verb mató) (NP (NPbase (Det un) (Nom (Noun elefante) "
     "(AdjP (Intens muy) (Adj gris))))) (Adv ayer)))"),
    # PP ambiguity: attached to the nearest noun (document, 1.4).
    ("Él mató un elefante en sus pijamas.",
     "(S (NP (NPbase (Prn él))) (VP (Verb mató) (NP (NPbase (Det un) (Nom (Noun elefante))) "
     "(PP (Prep en) (NP (NPbase (Pos sus) (Nom (Noun pijamas))))))))"),
    # Without an object, the PP goes to VP'.
    ("Ella duerme en la manzana.",
     "(S (NP (NPbase (Prn ella))) (VP (Verb duerme) (PP (Prep en) (NP (NPbase (Det la) (Nom (Noun manzana)))))))"),
    # "bajo" is Adj or Prep: only Prep fits after the verb.
    ("Ella duerme bajo el elefante.",
     "(S (NP (NPbase (Prn ella))) (VP (Verb duerme) (PP (Prep bajo) (NP (NPbase (Det el) (Nom (Noun elefante)))))))"),
])
def test_accepts_and_builds_the_flattened_tree(sentence, expected):
    tree, errors = tree_of(sentence)
    assert errors == []
    assert same_tree(tree, expected)
    assert tree_shape_errors(tree) == []


@pytest.mark.parametrize("sentence", [
    "Come la manzana.",                    # sujeto omitido
    "La manzana roja que comió ella.",     # subordinada, "que" is X
    "La niña.",                            # no verb
    "Ella come una.",                      # Det without noun
    "Niña la come.",                       # word order
])
def test_rejects_sentences_outside_the_grammar(sentence):
    tree, errors = tree_of(sentence)
    assert tree is None
    assert len(errors) == 1
    assert errors[0].error_type == "sintactico"


def test_agreement_is_not_the_parsers_job():
    # "La elefante grises duerme." has a valid STRUCTURE; agreement.py rejects it later.
    tree, errors = tree_of("La elefante grises duerme.")
    assert tree is not None and errors == []


def test_unknown_word_error_names_the_word():
    _, errors = tree_of("La manzana roja que comió ella.")
    assert errors[0].word == "que"
