"""Confusion matrices and classification reports (experiments/reports.py).

Skipped if the experiment dependencies (pandas, scikit-learn) are not installed.
"""

import pytest

pytest.importorskip("pandas")
pytest.importorskip("sklearn")

from evaluation.formats import Prediction, TestItem  # noqa: E402
from experiments import reports  # noqa: E402


def item(id_, tags, in_grammar=True, subject="ella", verb="come", obj=""):
    return TestItem(id_, 1, "X.", in_grammar, True, None if in_grammar else "sintactico",
                    ("svo",), tuple(tags), subject, verb, obj)


ITEMS = [
    item(1, [("ella", "Prn"), ("come", "Verb")]),
    item(2, [("los", "Det"), ("perros", "Noun"), ("come", "Verb")], in_grammar=False, subject="perros"),
    item(3, [("ella", "Prn"), ("duerme", "Verb")]),
]
PREDS = [
    Prediction(1, "spacy", None, tags=[["ella", "Prn"], ["come", "Verb"]], subject="ella", verb="come", object=""),
    Prediction(2, "spacy", None, tags=[["los", "Det"], ["perros", "Noun"], ["come", "Noun"]],
               subject="perros", verb="come", object=""),
    Prediction(3, "spacy", None, tags=[["ella", "Prn"]]),   # different length: left out
]


def test_tag_pairs_leave_out_misaligned_sentences():
    y_true, y_pred, skipped = reports.tag_pairs(ITEMS, PREDS)
    assert len(y_true) == len(y_pred) == 5
    assert skipped == [3]


def test_tag_confusion():
    y_true, y_pred, _ = reports.tag_pairs(ITEMS, PREDS)
    matrix = reports.tag_confusion(y_true, y_pred)
    assert list(matrix.index) == ["Prn", "Det", "Noun", "Verb"]     # agreed order
    assert matrix.loc["Verb", "Noun"] == 1 and matrix.loc["Verb", "Verb"] == 1
    assert matrix.values.sum() == 5


def test_tag_report():
    y_true, y_pred, _ = reports.tag_pairs(ITEMS, PREDS)
    report = reports.tag_report(y_true, y_pred)
    assert report.loc["Verb", "cobertura"] == pytest.approx(0.5)
    assert report.loc["Noun", "precision"] == pytest.approx(0.5)
    assert report.loc["exactitud", "f1"] == pytest.approx(4 / 5)
    assert {"promedio macro", "promedio ponderado"} <= set(report.index)


def test_acceptance_confusion_and_report():
    preds = [Prediction(1, "parser", True), Prediction(2, "parser", True), Prediction(3, "parser", None)]
    matrix = reports.acceptance_confusion(ITEMS, preds)
    assert matrix.loc["si", "acepta"] == 1 and matrix.loc["no", "acepta"] == 1
    assert matrix.values.sum() == 2                                   # acepta=None left out
    metrics = reports.acceptance_report(matrix)
    assert metrics["precision"] == pytest.approx(0.5)
    assert metrics["cobertura"] == 1
    assert metrics["rechazo_correcto"] == 0


def test_function_report():
    table = reports.function_report(ITEMS, PREDS)
    assert table.loc["verbo", "total"] == 2                             # id 3 has None
    assert table.loc["verbo", "exactitud"] == 1


def test_plot_confusion_saves_the_figure(tmp_path):
    pytest.importorskip("matplotlib")
    import matplotlib

    matplotlib.use("Agg")
    y_true, y_pred, _ = reports.tag_pairs(ITEMS, PREDS)
    path = tmp_path / "m.png"
    reports.plot_confusion(reports.tag_confusion(y_true, y_pred), "prueba", path)
    assert path.exists() and path.stat().st_size > 0
