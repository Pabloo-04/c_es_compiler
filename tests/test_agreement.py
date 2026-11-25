"""Agreement tests.  Owner: Person 5 (with P3). Fail with NotImplementedError until agreement.py is done.

The trees are built here by hand (from the lexicon) so they do not depend on the parser.
"""

from helpers import LEXICON
from spanish.agreement import check
from spanish.tokens import Token
from spanish.tree import Node


def build(bracketed: str) -> Node:
    """Bracketed tree -> Node whose leaves carry the reading of that category from the lexicon."""
    tree = Node.from_bracketed(bracketed)
    for position, leaf in enumerate(tree.leaves(), start=1):
        readings = LEXICON.lookup(leaf.word)
        leaf.token = Token(leaf.word, position, 1, readings)
        leaf.reading = next(r for r in readings if r.category.value == leaf.label)
    return tree


def test_agreeing_sentence():
    assert check(build("(O (SN (DET los) (SUST perros)) (SV (V corren)))")) == []


def test_det_noun_number():
    errors = check(build("(O (SN (DET el) (SUST gatos)) (SV (V comen)))"))
    assert len(errors) == 1 and errors[0].error_type == "concordancia"


def test_det_noun_gender():
    errors = check(build("(O (SN (DET la) (SUST gato)) (SV (V come)))"))
    assert len(errors) == 1


def test_noun_adjective_gender():
    errors = check(build("(O (SN (DET la) (SUST niña) (SA (ADJ negro))) (SV (V come)))"))
    assert len(errors) == 1
    assert errors[0].word == "negro"


def test_invariable_adjective_agrees_with_both_genders():
    # "grande" has no gender in the lexicon: it must not produce an error.
    assert check(build("(O (SN (DET la) (SUST casa) (SA (ADJ grande))) (SV (V come)))")) == []


def test_subject_verb_number():
    errors = check(build("(O (SN (DET los) (SUST niños)) (SV (V corre)))"))
    assert len(errors) == 1
    assert errors[0].word == "corre"


def test_subject_verb_person():
    # "nosotros" is 1st person plural; "comen" is 3rd person plural.
    errors = check(build("(O (SN (PRON nosotros)) (SV (V comen)))"))
    assert len(errors) == 1


def test_agreement_inside_the_object_too():
    errors = check(build("(O (SN (DET el) (SUST gato)) (SV (V come) (SN (DET las) (SUST comida))))"))
    assert len(errors) == 1
