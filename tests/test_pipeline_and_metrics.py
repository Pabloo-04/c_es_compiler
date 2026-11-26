"""Integration over the whole test set, and the metrics.

Owner: Person 5 (with P2 and P4). The pipeline test is the final check of
Phase 2: for every sentence of data/test_set.csv our system must give the
expected acepta / tipo_error and, when it parses, the expected tags and
syntactic functions.
"""

import pytest

from evaluation import metrics
from evaluation.formats import Prediction, TestItem, load_test_set
from spanish.grammar import tree_shape_errors
from spanish.pipeline import analyze, pp_attachment
from spanish.tree import Node

ITEMS = load_test_set()


@pytest.mark.parametrize("item", ITEMS, ids=[str(i.id) for i in ITEMS])
def test_parser_on_the_test_set(item):
    result = analyze(item.sentence)
    assert result.accepted == item.in_grammar, [str(e) for e in result.errors]
    assert result.error_type == item.error_type
    if result.tree is not None:
        assert tree_shape_errors(result.tree) == []
        assert [tuple(t) for t in result.tags] == list(item.tags)
        assert (result.subject, result.verb, result.object) == (item.subject, item.verb, item.object)


# ---------------------------------------------------------------------------
# Metrics (small hand-made case, docs/gramatica_es.md 2.7)
# ---------------------------------------------------------------------------
def item(id_, in_grammar, valid_spanish=None, level=1):
    valid = in_grammar if valid_spanish is None else valid_spanish
    return TestItem(id_, level, "X.", in_grammar, valid, None if in_grammar else "sintactico",
                    ("svo",), (("ella", "Prn"), ("come", "Verb")), "ella", "come", "")


PAIRS = [
    (item(1, True), Prediction(1, "parser", accepts=True)),     # TP
    (item(2, True), Prediction(2, "parser", accepts=False)),    # FN
    (item(3, False), Prediction(3, "parser", accepts=True)),    # FP
    (item(4, False), Prediction(4, "parser", accepts=False)),   # TN
    (item(5, False), Prediction(5, "parser", accepts=False)),   # TN
    (item(6, False), Prediction(6, "spacy", accepts=None)),     # excluded: no decision
]


def test_confusion():
    assert metrics.confusion(PAIRS) == {"TP": 1, "FP": 1, "FN": 1, "TN": 2}


def test_precision_coverage_and_rejection():
    assert metrics.precision(PAIRS) == pytest.approx(1 / 2)
    assert metrics.coverage(PAIRS) == pytest.approx(1 / 2)
    assert metrics.correct_rejection_rate(PAIRS) == pytest.approx(2 / 3)


def test_precision_without_acceptances_is_none():
    assert metrics.precision([(item(1, True), Prediction(1, "parser", accepts=False))]) is None


def test_against_valid_spanish():
    # The LLM accepts Spanish that the grammar does not generate (drift).
    pairs = [(item(1, False, valid_spanish=True), Prediction(1, "llm_zero", accepts=True))]
    assert metrics.precision(pairs, "in_grammar") == 0
    assert metrics.precision(pairs, "valid_spanish") == 1


def test_tagging_accuracy_and_length_mismatch():
    pairs = [
        (item(1, True), Prediction(1, "spacy", None, tags=[["ella", "Prn"], ["come", "Verb"]])),   # 2/2
        (item(2, True), Prediction(2, "spacy", None, tags=[["ella", "Prn"], ["come", "Noun"]])),   # 1/2
        (item(3, True), Prediction(3, "spacy", None, tags=[["ella", "Prn"]])),                     # mismatch
    ]
    assert metrics.tagging_accuracy(pairs) == pytest.approx(3 / 4)
    assert metrics.length_mismatches(pairs) == [3]


def test_function_accuracy():
    pairs = [
        (item(1, True), Prediction(1, "spacy", None, subject="ella", verb="come", object="")),
        (item(2, True), Prediction(2, "spacy", None, subject="", verb="come", object="")),
        (item(3, True), Prediction(3, "transformers", None)),                                     # excluded
    ]
    assert metrics.function_accuracy(pairs, "subject") == pytest.approx(1 / 2)
    assert metrics.function_accuracy(pairs, "verb") == 1


# ---------------------------------------------------------------------------
# PP attachment in the parser tree, and its metric (2.7 d)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("tree, expected", [
    # The parser's rule (document 1.4): with an object, the PP goes to the nearest noun.
    ("(S (NP (NPbase (Prn él))) (VP (Verb mató) (NP (NPbase (Det un) (Nom (Noun elefante))) "
     "(PP (Prep en) (NP (NPbase (Pos sus) (Nom (Noun pijamas))))))))", "sustantivo"),
    # Without an object, it goes to the verb (VP').
    ("(S (NP (NPbase (Det el) (Nom (Noun perro)))) (VP (Verb duerme) "
     "(PP (Prep en) (NP (NPbase (Pos sus) (Nom (Noun pijamas)))))))", "verbo"),
    ("(S (NP (NPbase (Prn ella))) (VP (Verb come)))", None),
])
def test_pp_attachment_from_the_tree(tree, expected):
    assert pp_attachment(Node.from_bracketed(tree)) == expected


def test_pp_attachment_accuracy():
    def pp_item(id_, gold):
        return TestItem(id_, 1, "X.", True, True, None, ("pp",), (("ella", "Prn"),), "ella", "come", "", gold)

    pairs = [
        (pp_item(1, "verbo"), Prediction(1, "parser", True, pp_attachment="sustantivo")),   # wrong
        (pp_item(2, "sustantivo"), Prediction(2, "parser", True, pp_attachment="sustantivo")),
        (pp_item(3, "ambigua"), Prediction(3, "parser", True, pp_attachment=None)),          # no answer: wrong
        (pp_item(4, None), Prediction(4, "parser", True, pp_attachment=None)),               # no PP: excluded
    ]
    assert metrics.pp_attachment_accuracy(pairs) == pytest.approx(1 / 3)
