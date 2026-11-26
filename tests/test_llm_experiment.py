"""LLM experiment: providers' helpers, the run loop and the analysis.

No API key is needed: a fake provider answers instead of the model, and the
results and the log go to a temporary folder. The sentences are written here,
so these tests do not depend on the size of data/test_set.csv.
"""

import json

import pytest

from evaluation import formats
from evaluation.formats import TestItem, load_predictions
from evaluation.run_parser import predict
from experiments import llm_analysis, llm_client, llm_experiment, prompts
from experiments.llm_client import Reply, read_log

BASE = {"id": "1", "nivel": "1", "oracion": "Ella come una manzana.", "en_gramatica": "si",
        "espanol_valido": "si", "tipo_error": "ninguno", "fenomeno": "svo",
        "etiquetas": "ella/Prn come/Verb una/Det manzana/Noun",
        "sujeto": "ella", "verbo": "come", "objeto": "manzana", "pp_adjunta": ""}

ITEMS = [
    TestItem.from_row(BASE),
    TestItem.from_row({**BASE, "id": "2", "nivel": "2", "oracion": "Los perros come.", "en_gramatica": "no",
                       "espanol_valido": "no", "tipo_error": "concordancia", "fenomeno": "concordancia_sv",
                       "etiquetas": "los/Det perros/Noun come/Verb", "sujeto": "perros", "objeto": ""}),
    TestItem.from_row({**BASE, "id": "3", "nivel": "3", "oracion": "Come la manzana.", "en_gramatica": "no",
                       "tipo_error": "sintactico", "fenomeno": "sujeto_omitido",
                       "etiquetas": "come/Verb la/Det manzana/Noun", "sujeto": ""}),
    TestItem.from_row({**BASE, "id": "4", "nivel": "3", "oracion": "Él mató un elefante en sus pijamas.",
                       "fenomeno": "ambiguedad;pp", "sujeto": "él", "verbo": "mató", "objeto": "elefante",
                       "etiquetas": "él/Prn mató/Verb un/Det elefante/Noun en/Prep sus/Pos pijamas/Noun",
                       "pp_adjunta": "ambigua"}),
]
PARSER = [predict(item) for item in ITEMS]
TREE = {p.id: p.tree for p in PARSER}


def answer(accepts, error=None, tree=None, **extra):
    return json.dumps({"acepta": accepts, "tipo_error": error, "etiquetas": [], "sujeto": "",
                       "verbo": "", "objeto": "", "pp_adjunta": None, "arbol": tree, **extra},
                      ensure_ascii=False)


ANSWERS = {
    "Ella come una manzana.": answer(True, tree=TREE[1]),
    "Los perros come.": "```json\n" + answer(False, "concordancia") + "\n```",
    # Drifts: correct Spanish outside our grammar, accepted with a tree of its own.
    "Come la manzana.": answer(True, tree="(S (VP (Verb come) (NP (NPbase (Det la) (Nom (Noun manzana))))))"),
    "Él mató un elefante en sus pijamas.": "Es una oración correcta.",   # not JSON
}


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Results in a temporary folder and a fake provider that answers by sentence."""
    monkeypatch.setattr(formats, "RESULTS_DIR", tmp_path)
    calls = []

    def fake(prompt, model, temperature):
        sentence = prompt.rstrip().rsplit("Oración: ", 1)[1]
        calls.append(sentence)
        return Reply(ANSWERS[sentence], input_tokens=1000, output_tokens=50)

    monkeypatch.setitem(llm_client.PROVIDERS, "fake", fake)
    return tmp_path / "llm.jsonl", calls


def run(system, log, **kwargs):
    return llm_experiment.run(system, ITEMS, provider="fake", model="m", log_path=log, **kwargs)


# ----------------------------------------------------------------------
# Few-shot examples
# ----------------------------------------------------------------------
@pytest.mark.parametrize("sentence, expected", prompts.EXAMPLES)
def test_examples_agree_with_our_parser(sentence, expected):
    got = predict(TestItem.from_row({**BASE, "oracion": sentence, "etiquetas": " ".join(
        f"{w}/{c}" for w, c in expected["etiquetas"]), "sujeto": "", "objeto": "",
        "verbo": expected["verbo"], "pp_adjunta": expected["pp_adjunta"] or "",
        "en_gramatica": "si" if expected["acepta"] else "no",
        "tipo_error": expected["tipo_error"] or "ninguno"}))
    assert (got.accepts, got.error_type) == (expected["acepta"], expected["tipo_error"])
    if expected["acepta"]:
        assert (got.tags, got.subject, got.verb, got.object, got.pp_attachment, got.tree) == (
            expected["etiquetas"], expected["sujeto"], expected["verbo"], expected["objeto"],
            expected["pp_adjunta"], expected["arbol"])


# ----------------------------------------------------------------------
# Answers -> result lines
# ----------------------------------------------------------------------
def test_not_json_is_recorded_as_such():
    p = llm_experiment.to_prediction(ITEMS[0], "No sé.", "llm_zero", 12.0)
    assert (p.accepts, p.run_error, p.time_ms) == (None, "respuesta_no_json", 12.0)


def test_fields_with_the_wrong_shape_become_null():
    raw = answer(True, tree="  ", etiquetas="ella/Prn come/Verb", sujeto=["ella"], verbo="Come")
    p = llm_experiment.to_prediction(ITEMS[0], raw, "llm_zero")
    assert (p.tags, p.subject, p.verb, p.tree, p.num_trees) == (None, None, "come", None, None)
    p.validate()


def test_error_type_only_when_rejecting():
    p = llm_experiment.to_prediction(ITEMS[0], answer(True, error="concordancia", tree=TREE[1]), "llm_zero")
    assert p.error_type is None and p.num_trees == 1
    p.validate()


# ----------------------------------------------------------------------
# Run loop
# ----------------------------------------------------------------------
def test_run_saves_results_and_logs_time_and_tokens(sandbox):
    log, calls = sandbox
    predictions = run("llm_zero", log)
    assert len(calls) == len(ITEMS) == len(predictions)
    assert [p.id for p in load_predictions("llm_zero")] == [i.id for i in ITEMS]
    entry = read_log(log)[0]
    assert entry["tokens_entrada"] == 1000 and entry["tokens_salida"] == 50 and "tiempo_ms" in entry


def test_rerun_reuses_the_log_and_keeps_the_call_time(sandbox):
    log, calls = sandbox
    first = run("llm_few", log)
    second = run("llm_few", log)
    assert len(calls) == len(ITEMS)                                  # no new calls
    assert [p.time_ms for p in first] == [p.time_ms for p in second]


def test_pilot_with_limit_does_not_save_but_is_reused(sandbox):
    log, calls = sandbox
    run("llm_zero", log, limit=2)
    assert len(calls) == 2
    assert not formats.results_path("llm_zero").exists()
    run("llm_zero", log)
    assert len(calls) == len(ITEMS)                                  # only the 2 missing ones


def test_few_shot_prompt_is_used_for_llm_few(sandbox):
    log, _ = sandbox
    run("llm_few", log, limit=1)
    assert "Ejemplos resueltos" in read_log(log)[0]["prompt"]


def test_retries_only_retryable_errors():
    attempts = []

    def flaky():
        attempts.append(1)
        if len(attempts) < 3:
            raise TimeoutError("503")
        return "ok"

    assert llm_client.with_retries(flaky, lambda e: isinstance(e, TimeoutError), sleep=lambda s: None) == "ok"
    with pytest.raises(KeyError):
        llm_client.with_retries(lambda: {}["x"], lambda e: isinstance(e, TimeoutError), sleep=lambda s: None)


# ----------------------------------------------------------------------
# Analysis
# ----------------------------------------------------------------------
def test_summary_numbers(sandbox):
    log, _ = sandbox
    s = llm_analysis.summary(ITEMS, run("llm_zero", log), PARSER)
    assert s["oraciones"] == 4 and s["sin_json"] == 1
    assert s["coincide_reglas"] == pytest.approx(2 / 3)    # 1 and 2 right, 3 wrong (4 has no decision)
    assert s["coincide_espanol"] == pytest.approx(3 / 3)   # it follows Spanish in all three
    assert s["desviacion"] == 1.0                          # 3: correct Spanish outside the grammar
    assert s["acepta_agramaticales"] == 0.0
    assert s["tipo_error_correcto"] == 1.0
    assert s["arbol_en_gramatica"] == pytest.approx(1 / 2)  # 3's tree has S without NP
    assert s["arbol_igual_parser"] == 1.0                   # 1 is the parser's tree


def test_groups_and_per_sentence(sandbox):
    log, _ = sandbox
    predictions = run("llm_zero", log)
    levels = {r["grupo"]: r for r in llm_analysis.by_group(ITEMS, predictions, "level")}
    assert levels[1]["coincide_reglas"] == 1.0 and levels[3]["coincide_reglas"] == 0.0
    phenomena = {r["grupo"]: r for r in llm_analysis.by_group(ITEMS, predictions, "phenomena")}
    assert phenomena["sujeto_omitido"]["desviacion"] == 1.0
    assert [r["id"] for r in llm_analysis.per_sentence(ITEMS, predictions) if r["desvio"]] == [3]


def test_answer_format_and_cost(sandbox):
    log, _ = sandbox
    run("llm_zero", log)
    run("llm_zero", log)                                   # reused: still one answer per id
    fmt = llm_analysis.answer_format(read_log(log), "llm_zero")
    assert fmt == {"respuestas": 4, "json_valido": 3, "json_puro": 2,
                   "json_con_bloque_de_codigo": 1, "sin_json": 1}
    (cost,) = llm_analysis.cost_from_log(read_log(log))
    assert (cost["sistema"], cost["modelo"], cost["llamadas"], cost["tokens_totales"]) == ("llm_zero", "m", 4, 4 * 1050)


def test_tree_follows_grammar():
    assert llm_analysis.tree_follows_grammar(TREE[1])
    assert not llm_analysis.tree_follows_grammar("(S (VP (Verb come)))")
    assert not llm_analysis.tree_follows_grammar("(S (NP")
    assert not llm_analysis.tree_follows_grammar(None)
