"""Metrics beyond the basic cases of test_pipeline_and_metrics.py (Person 4).

Small hand-made cases for each comparison of docs/gramatica_es.md 2.7, the
rows of results/metrics.csv and the report tables.
"""

from collections import Counter

import pytest

from evaluation import metrics
from evaluation.formats import Prediction, TestItem, load_test_set

TAGS = (("ella", "Prn"), ("come", "Verb"))


def item(id_, in_grammar=True, valid_spanish=None, level=1, error=None, pp=None, tags=TAGS):
    valid = in_grammar if valid_spanish is None else valid_spanish
    error = None if in_grammar else (error or "sintactico")
    return TestItem(id_, level, "X.", in_grammar, valid, error, ("svo",), tags, "ella", "come", "", pp)


# ---------------------------------------------------------------------------
# a) Acceptance
# ---------------------------------------------------------------------------
def test_run_error_counts_as_wrong_answer():
    # An LLM answer that is not JSON: acepta null + error_ejecucion -> wrong, not excluded.
    pairs = [
        (item(1, True), Prediction(1, "llm_zero", None, run_error="respuesta_no_json")),
        (item(2, False), Prediction(2, "llm_zero", None, run_error="respuesta_no_json")),
        (item(3, True), Prediction(3, "llm_zero", True)),
    ]
    assert metrics.confusion(pairs) == {"TP": 1, "FP": 1, "FN": 1, "TN": 0}
    assert metrics.run_errors(pairs) == 2


def test_accuracy_and_f1():
    pairs = [
        (item(1, True), Prediction(1, "parser", True)),
        (item(2, True), Prediction(2, "parser", False)),
        (item(3, False), Prediction(3, "parser", False)),
        (item(4, False), Prediction(4, "parser", True)),
    ]
    assert metrics.acceptance_accuracy(pairs) == pytest.approx(0.5)
    assert metrics.f1(pairs) == pytest.approx(0.5)
    assert metrics.f1([(item(1, True), Prediction(1, "parser", False))]) is None


def test_unknown_reference():
    with pytest.raises(ValueError):
        metrics.confusion([(item(1), Prediction(1, "parser", True))], "otra")


def test_error_type():
    pairs = [
        (item(1, False, error="concordancia"), Prediction(1, "parser", False, "concordancia")),
        (item(2, False, error="concordancia"), Prediction(2, "parser", False, "sintactico")),
        (item(3, False, error="sintactico"), Prediction(3, "parser", True)),            # accepted: not counted
        (item(4, False, error="sintactico"), Prediction(4, "llm_few", False)),           # no type
        (item(5, True), Prediction(5, "parser", True)),                                  # in grammar: not counted
    ]
    assert metrics.error_type_accuracy(pairs) == pytest.approx(1 / 3)
    assert metrics.error_type_confusion(pairs) == Counter({
        ("concordancia", "concordancia"): 1, ("concordancia", "sintactico"): 1,
        ("sintactico", "acepta"): 1, ("sintactico", "sin_tipo"): 1,
    })


# ---------------------------------------------------------------------------
# b) Tagging
# ---------------------------------------------------------------------------
def test_per_category_and_confusion():
    tags = (("el", "Det"), ("perro", "Noun"), ("negro", "Adj"))
    pairs = [
        (item(1, tags=tags), Prediction(1, "spacy", None, tags=[["el", "Det"], ["perro", "Noun"], ["negro", "Noun"]])),
        (item(2, tags=tags), Prediction(2, "spacy", None, tags=[["el", "Det"], ["perro", "Noun"], ["negro", "Adj"]])),
        (item(3, tags=tags), Prediction(3, "spacy", None, tags=[["el", "Det"]])),   # mismatch: left out
        (item(4, tags=tags), Prediction(4, "parser", False)),                        # no tags: left out
    ]
    assert metrics.tag_confusion(pairs) == Counter({
        ("Det", "Det"): 2, ("Noun", "Noun"): 2, ("Adj", "Noun"): 1, ("Adj", "Adj"): 1})
    by_category = metrics.per_category(pairs)
    assert by_category["Noun"] == {"precision": pytest.approx(2 / 3), "cobertura": 1.0}
    assert by_category["Adj"] == {"precision": 1.0, "cobertura": 0.5}
    assert by_category["Prep"] == {"precision": None, "cobertura": None}
    assert metrics.length_mismatches(pairs) == [3]


# ---------------------------------------------------------------------------
# c) and d)
# ---------------------------------------------------------------------------
def test_function_accuracy_ignores_case():
    pairs = [(item(1), Prediction(1, "llm_zero", True, subject="Ella"))]
    assert metrics.function_accuracy(pairs, "subject") == 1


def test_ambiguity_detection_and_pp_confusion():
    pairs = [
        (item(1, pp="ambigua"), Prediction(1, "llm_few", True, pp_attachment="ambigua")),
        (item(2, pp="ambigua"), Prediction(2, "llm_few", True, pp_attachment="sustantivo")),
        (item(3, pp="verbo"), Prediction(3, "llm_few", True)),
        (item(4), Prediction(4, "llm_few", True)),
    ]
    assert metrics.ambiguity_detection(pairs) == 0.5
    assert metrics.ambiguity_detection([(item(1), Prediction(1, "parser", True))]) is None
    assert metrics.pp_confusion(pairs) == Counter({
        ("ambigua", "ambigua"): 1, ("ambigua", "sustantivo"): 1, ("verbo", "sin_respuesta"): 1})


def test_mean_time():
    pairs = [(item(1), Prediction(1, "parser", True, time_ms=2)), (item(2), Prediction(2, "parser", True, time_ms=4))]
    assert metrics.mean_time_ms(pairs) == 3


# ---------------------------------------------------------------------------
# Rows of metrics.csv
# ---------------------------------------------------------------------------
def _rows(system, pairs):
    return {(r["comparacion"], r["nivel"], r["metrica"]): r["valor"] for r in metrics.metric_rows(system, pairs)}


def test_metric_rows_skip_what_a_system_does_not_do():
    spacy = _rows("spacy", [(item(1, pp="verbo"), Prediction(1, "spacy", None, tags=[list(t) for t in TAGS],
                                                             pp_attachment="verbo"))])
    assert not any(k[0].startswith("aceptacion") for k in spacy)          # spaCy never decides
    assert spacy[("estructura", "todos", "pp_adjunta")] == 1
    transformers = _rows("transformers", [(item(1, pp="verbo"), Prediction(1, "transformers", True))])
    assert ("aceptacion", "todos", "exactitud") in transformers
    assert ("aceptacion", "todos", "tipo_error") not in transformers       # never says why
    assert not any(k[0] == "estructura" for k in transformers)            # never computes the PP


def test_metric_rows_by_level_and_category():
    rows = _rows("parser", [
        (item(1, level=1), Prediction(1, "parser", True, tags=[list(t) for t in TAGS])),
        (item(2, False, level=3), Prediction(2, "parser", False, "sintactico")),
    ])
    assert rows[("aceptacion", "1", "exactitud")] == 1
    assert rows[("aceptacion", "3", "rechazo_correcto")] == 1
    assert ("aceptacion", "2", "exactitud") not in rows                   # no sentences of level 2
    assert rows[("etiquetado_categoria", "todos", "cobertura_Verb")] == 1


def test_outdated_results_are_skipped(tmp_path, monkeypatch):
    import evaluation.formats as formats

    items = [item(1), item(2)]
    monkeypatch.setattr(formats, "RESULTS_DIR", tmp_path)
    formats.write_jsonl(tmp_path / "spacy.jsonl", [Prediction(1, "spacy", None).to_json()])
    warnings = []
    assert metrics.load_all_pairs(items, warn=warnings.append) == {}
    assert "spacy" in warnings[0] and "volver a correrlo" in warnings[0]


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
def test_tables_render():
    items = [item(1), item(2, False, valid_spanish=True, level=3, pp="verbo")]
    all_pairs = {"parser": metrics.align(items, [Prediction(1, "parser", True, tags=[list(t) for t in TAGS]),
                                                 Prediction(2, "parser", False, "sintactico")])}
    rows = metrics.compute_all(all_pairs)
    tables = metrics.build_tables(items, rows, all_pairs)
    title, header, body = tables["aceptacion"]
    assert body[0][0] == "Parser propio" and "Precisión" in header
    md = metrics.markdown_table(header, body)
    assert "| Parser propio | 1.00 |" in md
    tex = metrics.latex_table(header, body)
    assert tex.startswith(r"\begin{tabular}") and r"\bottomrule" in tex
    assert tables["set_de_prueba"][2][-1][1:6] == [2, 1, 1, 1, 1]           # total row
    assert metrics.latex_table(["a"], []) == "\\pendiente{sin datos}\n"


def test_fmt():
    assert metrics.fmt(None) == "—"
    assert metrics.fmt(0.5) == "0.50"
    assert metrics.fmt(123.456) == "123.5"
    assert metrics.fmt(3) == "3"


# ---------------------------------------------------------------------------
# The real test set (P4): size and balance required by the assignment
# ---------------------------------------------------------------------------
def test_test_set_size_and_balance():
    items = load_test_set()
    assert len(items) >= 60
    for level in (1, 2, 3):
        assert sum(i.level == level for i in items) >= 15
    assert all(i.in_grammar for i in items if i.level == 1)          # level 1: the grammar must accept
    assert sum(not i.in_grammar for i in items) >= 15                 # rejection is tested too
    assert {i.error_type for i in items if i.error_type} == {"sintactico", "concordancia"}
    assert any(i.valid_spanish and not i.in_grammar for i in items)   # rules vs. knowledge of Spanish
    assert {i.pp_attachment for i in items if i.pp_attachment} == {"sustantivo", "verbo", "ambigua"}


def test_every_phenomenon_is_tested():
    from evaluation.formats import PHENOMENA

    used = {p for i in load_test_set() for p in i.phenomena}
    assert used == set(PHENOMENA)


def test_sentences_are_unique():
    sentences = [i.sentence.lower() for i in load_test_set()]
    assert len(sentences) == len(set(sentences))
