"""Results format and LLM prompt helpers. These pass from day 1."""

import pytest

from evaluation.formats import Prediction, TestItem, load_test_set
from experiments import prompts


def test_prediction_round_trip():
    p = Prediction("S001", "parser", True, "(O (SN (PRON ella)) (SV (V come)))", ["PRON", "V"])
    assert Prediction.from_json(p.to_json()) == p


def test_covered_item_needs_a_tree():
    with pytest.raises(ValueError):
        TestItem.from_json({"id": "X", "nivel": "simple", "oracion": "a", "gramatical": True,
                            "cubierta": True, "arbol": None, "tipo_error": None})


def test_not_covered_item_needs_an_error_type():
    with pytest.raises(ValueError):
        TestItem.from_json({"id": "X", "nivel": "simple", "oracion": "a", "gramatical": False,
                            "cubierta": False, "arbol": None, "tipo_error": None})


def test_zero_shot_prompt_contains_the_grammar_and_the_sentence():
    text = prompts.zero_shot("el gato come")
    assert "SN" in text and "Oración: el gato come" in text


def test_few_shot_never_includes_the_target_sentence():
    items = load_test_set()
    with pytest.raises(ValueError):
        prompts.few_shot(items[0].sentence, items[:3])
    text = prompts.few_shot(items[0].sentence, items[1:3])
    assert text.count("Oración:") == 3  # two examples + the question


def test_parse_accepted_answer():
    answer = "ACEPTADA: sí\nARBOL: (O (SN (DET el) (SUST gato)) (SV (V come)))\nEXPLICACION: ok"
    parsed = prompts.parse_answer(answer)
    assert parsed["aceptada"] is True
    assert parsed["arbol"].startswith("(O")
    assert parsed["formato_valido"]


def test_parse_rejected_answer():
    parsed = prompts.parse_answer("aceptada: no\nerror: Concordancia\nexplicacion: número")
    assert (parsed["aceptada"], parsed["tipo_error"], parsed["formato_valido"]) == (False, "concordancia", True)


def test_parse_free_text_answer_is_invalid():
    parsed = prompts.parse_answer("La oración es correcta en español.")
    assert parsed["aceptada"] is None and not parsed["formato_valido"]
