"""Integration over the whole test set, and the metrics.

Owner: Person 5 (with P2 and P4). The pipeline test is the final check of
Phase 2: our parser must accept exactly the covered sentences, with the
expected tree, and reject the others with the expected error type.
"""

import pytest

from evaluation import metrics
from evaluation.formats import Prediction, TestItem, load_test_set
from spanish.pipeline import analyze
from spanish.tree import same_tree

ITEMS = load_test_set()


@pytest.mark.parametrize("item", ITEMS, ids=[i.id for i in ITEMS])
def test_parser_on_the_test_set(item):
    result = analyze(item.sentence)
    assert result.accepted == item.covered, [str(e) for e in result.errors]
    if item.covered:
        assert same_tree(result.tree, item.tree)
    else:
        assert result.error_type == item.error_type


# ---------------------------------------------------------------------------
# Metrics (small hand-made case)
# ---------------------------------------------------------------------------
def item(id_, covered, grammatical=True, tree="(O (SN (PRON ella)) (SV (V come)))", error=None):
    return TestItem(id_, "simple", "x", grammatical, covered, tree if covered else None,
                    None if covered else (error or "sintactico"))


PAIRS = [
    (item("A", True), Prediction("A", "s", accepted=True)),            # true accept
    (item("B", True), Prediction("B", "s", accepted=False)),           # wrong reject
    (item("C", False), Prediction("C", "s", accepted=True)),           # wrong accept
    (item("D", False), Prediction("D", "s", accepted=False)),          # true reject
    (item("E", False), Prediction("E", "s", accepted=False)),          # true reject
]


def test_precision():
    assert metrics.precision(PAIRS) == pytest.approx(1 / 2)


def test_coverage():
    assert metrics.coverage(PAIRS) == pytest.approx(1 / 2)


def test_correct_rejection_rate():
    assert metrics.correct_rejection_rate(PAIRS) == pytest.approx(2 / 3)


def test_precision_without_acceptances_is_none():
    assert metrics.precision([(item("A", True), Prediction("A", "s", accepted=False))]) is None


# TODO(P5 con P4): tree_accuracy, tagging_accuracy, error_confusion, by_level.
