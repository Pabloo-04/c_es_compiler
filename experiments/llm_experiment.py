"""LLM experiment: does the model follow our production rules?  Owner: Person 5.

This is the `experimento_llm.py` of the assignment. notebooks/llm_experiment.ipynb
uses it, and it also runs from the terminal:

    python -m experiments.llm_experiment --proveedor gemini --modelo gemini-3.8-flash --limite 3
    python -m experiments.llm_experiment --proveedor gemini --modelo gemini-3.8-flash --pausa 5

Two versions (experiments/prompts.py):
  - llm_zero: rules + lexicon only.
  - llm_few:  the same + the fixed EXAMPLES (not sentences of the test set).

Outputs (docs/gramatica_es.md, 2.4 and 2.6): results/llm_zero.jsonl,
results/llm_few.jsonl and results/logs/llm.jsonl. Every answer goes to the log
first, and an answer already in the log is reused, so an interrupted run
continues where it stopped when it is started again.
"""

import argparse
import time

from evaluation.formats import LLM_LOG_PATH, Prediction, TestItem, load_test_set, save_predictions

from . import prompts
from .llm_client import ask_llm, find_in_log

SYSTEMS = {"llm_zero": prompts.zero_shot, "llm_few": prompts.few_shot}


def to_prediction(item: TestItem, raw: str, system: str, time_ms: float = 0.0) -> Prediction:
    """One result line from a raw answer (docs/gramatica_es.md, 2.6).

    Not JSON (or missing keys): "acepta": null and "error_ejecucion":
    "respuesta_no_json". Values outside the agreed sets are kept as given
    (they count as wrong in the metrics); only fields with the wrong SHAPE are
    dropped to null, so that one odd field does not discard the whole answer.
    """
    answer = prompts.parse_answer(raw)
    if answer is None:
        return Prediction(item.id, system, accepts=None, time_ms=time_ms, run_error="respuesta_no_json")
    accepts = answer["acepta"]
    tree = answer["arbol"] if isinstance(answer["arbol"], str) and answer["arbol"].strip() else None
    return Prediction(
        item.id, system,
        accepts=accepts,
        error_type=_text(answer["tipo_error"]) if accepts is False else None,
        tags=_tags(answer["etiquetas"]),
        subject=_text(answer["sujeto"]),
        verb=_text(answer["verbo"]),
        object=_text(answer["objeto"]),
        pp_attachment=_text(answer["pp_adjunta"]),
        tree=tree,
        num_trees=1 if tree else None,
        time_ms=time_ms,
    )


def _text(value) -> str | None:
    return value.strip().lower() if isinstance(value, str) else None


def _tags(value) -> list[list[str]] | None:
    """[["ella", "Prn"], ...] or None if the LLM sent something with another shape."""
    if not isinstance(value, list):
        return None
    if not all(isinstance(pair, list) and len(pair) == 2 and all(isinstance(x, str) for x in pair)
               for pair in value):
        return None
    return [[word.lower(), category] for word, category in value]


def run(
    system: str,
    items: list[TestItem],
    *,
    provider: str = "manual",
    model: str = "manual",
    temperature: float = 0,
    pause: float = 0.0,
    limit: int | None = None,
    log_path=LLM_LOG_PATH,
) -> list[Prediction]:
    """Ask the LLM about every sentence and save results/<system>.jsonl.

    - pause: seconds before each NEW call (free tiers limit requests per minute).
      Answers reused from the log do not wait.
    - limit: make at most this many new calls and do not save the results file
      (the format needs every sentence); useful as a pilot. The answers stay in
      the log and are reused by the full run.
    """
    build_prompt = SYSTEMS[system]
    predictions = []
    new_calls = 0
    for item in items:
        cached = find_in_log(item.id, system, log_path, model=model)
        if cached is None:
            if limit is not None and new_calls >= limit:
                break
            if new_calls and pause:
                time.sleep(pause)
            new_calls += 1
        start = time.perf_counter()
        raw = ask_llm(build_prompt(item.sentence), id=item.id, system=system,
                      provider=provider, model=model, temperature=temperature, log_path=log_path)
        # Time of the real API call (kept in the log), so a rerun reports the same.
        entry = find_in_log(item.id, system, log_path, model=model) or {}
        time_ms = entry.get("tiempo_ms", (time.perf_counter() - start) * 1000)
        prediction = to_prediction(item, raw, system, time_ms)
        predictions.append(prediction)
        state = "sin JSON" if prediction.accepts is None else ("acepta" if prediction.accepts else "rechaza")
        print(f"  {system} {item.id}: {state}{' (del log)' if cached else ''}")
    if limit is None:
        print("Guardado en", save_predictions(system, predictions, items))
    else:
        print(f"Prueba con límite: {len(predictions)} de {len(items)} oraciones; no se guarda {system}.jsonl")
    return predictions


def main() -> None:
    parser = argparse.ArgumentParser(description="Experimento con el LLM (zero-shot y few-shot)")
    parser.add_argument("--proveedor", default="manual", help="manual | gemini | anthropic")
    parser.add_argument("--modelo", default="manual", help="nombre EXACTO del modelo (va al log y al informe)")
    parser.add_argument("--temperatura", type=float, default=0.0)
    parser.add_argument("--sistema", choices=(*SYSTEMS, "ambos"), default="ambos")
    parser.add_argument("--pausa", type=float, default=0.0, help="segundos antes de cada llamada nueva")
    parser.add_argument("--limite", type=int, help="máximo de llamadas nuevas por sistema (prueba piloto)")
    args = parser.parse_args()
    if args.proveedor != "manual" and args.modelo == "manual":
        parser.error("con una API hay que dar --modelo con el nombre exacto del modelo")

    items = load_test_set()
    print(f"{len(items)} oraciones; proveedor {args.proveedor}, modelo {args.modelo}")
    for system in SYSTEMS if args.sistema == "ambos" else (args.sistema,):
        run(system, items, provider=args.proveedor, model=args.modelo,
            temperature=args.temperatura, pause=args.pausa, limit=args.limite)


if __name__ == "__main__":
    main()
