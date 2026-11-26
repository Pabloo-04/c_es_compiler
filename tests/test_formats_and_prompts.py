"""Test set and results format (docs/gramatica_es.md, Part 2) and the LLM prompts.
These pass from day 1."""

import json

import pytest

from evaluation.formats import Prediction, TestItem, load_test_set, save_predictions
from experiments import prompts
from experiments.llm_client import ask_llm, find_in_log
from spanish.grammar import tree_shape_errors
from spanish.tree import Node

ROW = {
    "id": "1", "nivel": "1", "oracion": "Ella come una manzana.", "en_gramatica": "si",
    "espanol_valido": "si", "tipo_error": "ninguno", "fenomeno": "svo",
    "etiquetas": "ella/Prn come/Verb una/Det manzana/Noun",
    "sujeto": "ella", "verbo": "come", "objeto": "manzana",
}


# ---------------------------------------------------------------------------
# Test set rows
# ---------------------------------------------------------------------------
def test_valid_row():
    item = TestItem.from_row(ROW)
    assert item.tags[0] == ("ella", "Prn") and item.error_type is None and item.in_grammar


@pytest.mark.parametrize("change", [
    {"etiquetas": "ella/Prn come/Verb una/Det"},                  # fewer tags than words
    {"etiquetas": "ella/Prn come/VERB una/Det manzana/Noun"},     # unknown category
    {"tipo_error": "concordancia"},                                # in grammar with an error
    {"en_gramatica": "no"},                                        # not in grammar without error type
    {"espanol_valido": "no"},                                      # grammar accepting bad Spanish
    {"oracion": "ella come una manzana"},                          # no capital, no period
    {"oracion": "Ella come, una manzana."},                        # comma
    {"fenomeno": "sujeto"},                                        # unknown phenomenon
    {"nivel": "4"},
    {"sujeto": "perro"},                                           # not a word of the sentence
])
def test_invalid_rows(change):
    with pytest.raises(ValueError):
        TestItem.from_row({**ROW, **change})


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
def test_prediction_json_uses_the_agreed_keys():
    p = Prediction(1, "parser", True, tags=[["ella", "Prn"]], subject="ella", verb="come", object="")
    keys = list(p.to_json())
    assert keys == ["id", "sistema", "acepta", "tipo_error", "etiquetas", "sujeto", "verbo",
                    "objeto", "arbol", "num_arboles", "tiempo_ms", "error_ejecucion"]
    assert Prediction.from_json(p.to_json()) == p


def test_save_requires_every_id_in_order(tmp_path, monkeypatch):
    import evaluation.formats as formats

    monkeypatch.setattr(formats, "RESULTS_DIR", tmp_path)
    items = load_test_set()
    predictions = [Prediction(i.id, "spacy", None) for i in items]
    assert save_predictions("spacy", predictions, items).exists()
    with pytest.raises(ValueError):
        save_predictions("spacy", list(reversed(predictions)), items)
    with pytest.raises(ValueError):
        save_predictions("spacy", predictions[:-1], items)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
def test_zero_shot_prompt_has_grammar_lexicon_and_sentence():
    text = prompts.zero_shot("Ella come una manzana.")
    assert "NPbase  → Prn | Det Nom | Pos Nom" in text
    assert "elefante" in text and "Oración: Ella come una manzana." in text


def test_few_shot_examples_are_not_in_the_test_set():
    test_sentences = {i.sentence for i in load_test_set()}
    assert not test_sentences & {s for s, _ in prompts.EXAMPLES}


def test_few_shot_examples_are_valid_answers():
    for sentence, answer in prompts.EXAMPLES:
        assert prompts.parse_answer(json.dumps(answer)) == answer
        if answer["arbol"]:
            assert tree_shape_errors(Node.from_bracketed(answer["arbol"])) == [], sentence


def test_few_shot_never_includes_the_question():
    with pytest.raises(ValueError):
        prompts.few_shot(prompts.EXAMPLES[0][0])


def test_parse_answer():
    good = json.dumps({"acepta": False, "tipo_error": "concordancia", "etiquetas": [], "sujeto": "",
                       "verbo": "come", "objeto": "", "arbol": None})
    assert prompts.parse_answer(good)["tipo_error"] == "concordancia"
    assert prompts.parse_answer("La oración es correcta.") is None
    assert prompts.parse_answer('{"acepta": true}') is None                  # missing keys
    assert prompts.parse_answer("```json\n" + good + "\n```") is None        # strict (TODO P5)


# ---------------------------------------------------------------------------
# LLM log and cache
# ---------------------------------------------------------------------------
def test_ask_llm_logs_and_reuses_the_answer(tmp_path, monkeypatch):
    import experiments.llm_client as client

    calls = []
    monkeypatch.setitem(client.PROVIDERS, "fake", lambda prompt, model, t: calls.append(prompt) or '{"x": 1}')
    log = tmp_path / "llm.jsonl"
    first = ask_llm("p", id=1, system="llm_zero", provider="fake", model="m", log_path=log)
    second = ask_llm("p", id=1, system="llm_zero", provider="fake", model="m", log_path=log)
    assert first == second == '{"x": 1}' and len(calls) == 1
    entry = find_in_log(1, "llm_zero", log)
    assert set(entry) == {"id", "sistema", "modelo", "temperature", "prompt", "respuesta_cruda", "fecha"}
