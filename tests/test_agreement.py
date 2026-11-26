"""Agreement tests.  Owner: Person 5 (with P3). Fail with NotImplementedError until agreement.py is done.

Trees are built by hand from the lexicon, so they do not depend on the parser.
Rules: docs/gramatica_es.md, section 1.3.
"""

from helpers import tree_from_lexicon as build
from spanish.agreement import check


def test_agreeing_sentence():
    assert check(build("(S (NP (NPbase (Det los) (Nom (Noun perros) (AdjP (Adj rojos))))) (VP (Verb comen)))")) == []


def test_det_noun_gender():
    # "la elefante" ✘
    errors = check(build("(S (NP (NPbase (Det la) (Nom (Noun elefante)))) (VP (Verb duerme)))"))
    assert len(errors) == 1 and errors[0].error_type == "concordancia"


def test_det_noun_number():
    # "los perro" ✘
    assert len(check(build("(S (NP (NPbase (Det los) (Nom (Noun perro)))) (VP (Verb duerme)))"))) == 1


def test_document_example_reports_the_adjective_too():
    # "La elefante grises duerme.": gender (la/elefante) and number (grises/elefante).
    errors = check(build("(S (NP (NPbase (Det la) (Nom (Noun elefante) (AdjP (Adj grises))))) (VP (Verb duerme)))"))
    assert len(errors) == 2
    assert "grises" in {e.word for e in errors}


def test_invariable_adjective_agrees_with_both_genders():
    # "grande" has no gender in the lexicon.
    assert check(build("(S (NP (NPbase (Det la) (Nom (Noun niña) (AdjP (Adj grande))))) (VP (Verb duerme)))")) == []


def test_possessive_checks_only_number():
    assert check(build("(S (NP (NPbase (Pos mi) (Nom (Noun niña)))) (VP (Verb duerme)))")) == []
    assert len(check(build("(S (NP (NPbase (Pos sus) (Nom (Noun perro)))) (VP (Verb duerme)))"))) == 1


def test_subject_verb_number():
    # "Los perros come." ✘
    errors = check(build("(S (NP (NPbase (Det los) (Nom (Noun perros)))) (VP (Verb come)))"))
    assert len(errors) == 1
    assert errors[0].word == "come"


def test_subject_verb_person():
    # "yo" is 1st person; "come" is 3rd person.
    assert len(check(build("(S (NP (NPbase (Prn yo))) (VP (Verb come)))"))) == 1


def test_agreement_inside_the_object_and_inside_pps():
    obj = "(S (NP (NPbase (Prn ella))) (VP (Verb come) (NP (NPbase (Det las) (Nom (Noun manzana))))))"
    pp = "(S (NP (NPbase (Prn él))) (VP (Verb duerme) (PP (Prep en) (NP (NPbase (Det los) (Nom (Noun manzana)))))))"
    assert len(check(build(obj))) == 1
    assert len(check(build(pp))) == 1
