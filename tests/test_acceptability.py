"""Threshold calibration for the grammaticality judgements (experiments/acceptability.py).

Only the pure-Python part is tested here; scoring needs the BETO model and is
exercised in notebooks/nlp_comparison.ipynb.
"""

import csv
from pathlib import Path

import pytest

from evaluation.formats import load_test_set
from experiments.acceptability import calibrate_threshold

CALIBRATION = Path(__file__).resolve().parent.parent / "data" / "calibration_acceptability.csv"


def test_threshold_separates_perfectly_separable_scores():
    threshold, accuracy = calibrate_threshold([-1.0, -2.0, -5.0, -6.0], [True, True, False, False])
    assert accuracy == 1
    assert -5.0 < threshold < -2.0
    assert threshold == pytest.approx(-3.5)       # midpoint: largest margin


def test_threshold_with_overlap_maximizes_accuracy():
    scores = [-1.0, -3.0, -2.0, -4.0]
    labels = [True, False, True, True]             # -3.0 is a bad sentence scored high
    threshold, accuracy = calibrate_threshold(scores, labels)
    assert accuracy == pytest.approx(3 / 4)


def test_threshold_rejects_bad_input():
    with pytest.raises(ValueError):
        calibrate_threshold([], [])
    with pytest.raises(ValueError):
        calibrate_threshold([-1.0], [True, False])


def test_calibration_set_is_balanced_minimal_pairs_outside_the_test_set():
    rows = list(csv.DictReader(CALIBRATION.open(encoding="utf-8")))
    test_sentences = {item.sentence for item in load_test_set()}
    assert not {r["oracion"] for r in rows} & test_sentences
    pairs = {}
    for r in rows:
        pairs.setdefault(r["par"], []).append(r["espanol_valido"])
    assert all(sorted(v) == ["no", "si"] for v in pairs.values())
