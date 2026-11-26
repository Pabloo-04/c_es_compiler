"""Metrics to compare the systems.  Owner: Person 4.

    python -m evaluation.metrics        # writes results/metrics.csv for every system with results

Definitions: docs/gramatica_es.md, section 2.7. Three comparisons; each
system takes part in the ones it has data for (None values are excluded):

  a) Acceptance (parser and LLM): `acepta` against `en_gramatica`
     (and, for the LLM, also against `espanol_valido`).
         precision          = TP / (TP + FP)
         coverage (recall)  = TP / (TP + FN)
         correct rejection  = TN / (TN + FP)
  b) Tagging (every system): tags word by word against `etiquetas`.
         accuracy = right words / total words; precision and recall per category;
         a sentence with a different number of words counts as a tagging
         error and is reported apart.
  c) Syntactic functions: `sujeto`, `verbo`, `objeto`, exact match.
  d) PP attachment (parser, spaCy, LLM): `pp_adjunta` against the test set,
     only on sentences with a PP; a None prediction counts as wrong.

Output: results/metrics.csv with the columns
    sistema,comparacion,nivel,metrica,valor
where nivel is 1, 2, 3 or "todos".
"""

import csv
from collections.abc import Callable

from .formats import (
    LEVELS,
    METRICS_PATH,
    SYSTEMS,
    Prediction,
    TestItem,
    load_predictions,
    load_test_set,
    results_path,
)

Pair = tuple[TestItem, Prediction]


def align(items: list[TestItem], predictions: list[Prediction]) -> list[Pair]:
    """Pair each test item with its prediction (same id). Missing ids raise."""
    by_id = {p.id: p for p in predictions}
    missing = [i.id for i in items if i.id not in by_id]
    if missing:
        raise ValueError(f"faltan resultados para los ids {missing}")
    return [(item, by_id[item.id]) for item in items]


# ----------------------------------------------------------------------
# a) Acceptance
# ----------------------------------------------------------------------
def confusion(pairs: list[Pair], reference: str = "in_grammar") -> dict[str, int]:
    """{"TP": .., "FP": .., "FN": .., "TN": ..} of `acepta` against the reference.

    reference: "in_grammar" (en_gramatica) or "valid_spanish" (espanol_valido).
    Predictions with accepts None (the system does not decide) are excluded.
    """
    # TODO(P4). Hint: getattr(item, reference) gives the expected value.
    raise NotImplementedError("TODO(P4): confusion")


def precision(pairs: list[Pair], reference: str = "in_grammar") -> float | None:
    """TP / (TP + FP). None if the denominator is 0."""
    # TODO(P4)
    raise NotImplementedError("TODO(P4): precision")


def coverage(pairs: list[Pair], reference: str = "in_grammar") -> float | None:
    """TP / (TP + FN)."""
    # TODO(P4)
    raise NotImplementedError("TODO(P4): coverage")


def correct_rejection_rate(pairs: list[Pair], reference: str = "in_grammar") -> float | None:
    """TN / (TN + FP)."""
    # TODO(P4)
    raise NotImplementedError("TODO(P4): correct_rejection_rate")


# ----------------------------------------------------------------------
# b) Tagging
# ----------------------------------------------------------------------
def tagging_accuracy(pairs: list[Pair]) -> float | None:
    """Right words / total words, over the sentences with the same number of
    words as expected. None if no sentence can be compared."""
    # TODO(P4)
    raise NotImplementedError("TODO(P4): tagging_accuracy")


def length_mismatches(pairs: list[Pair]) -> list[int]:
    """ids where the system produced a different number of words (reported apart)."""
    # TODO(P4)
    raise NotImplementedError("TODO(P4): length_mismatches")


def per_category(pairs: list[Pair]) -> dict[str, dict[str, float | None]]:
    """{"Adj": {"precision": .., "cobertura": ..}, ...} for every category."""
    # TODO(P4)
    raise NotImplementedError("TODO(P4): per_category")


# ----------------------------------------------------------------------
# c) Syntactic functions
# ----------------------------------------------------------------------
def function_accuracy(pairs: list[Pair], field: str) -> float | None:
    """field: "subject", "verb" or "object". Exact match; None predictions excluded."""
    # TODO(P4)
    raise NotImplementedError("TODO(P4): function_accuracy")


# ----------------------------------------------------------------------
# d) PP attachment
# ----------------------------------------------------------------------
def pp_attachment_accuracy(pairs: list[Pair]) -> float | None:
    """Sentences whose expected pp_adjunta is not None: share where the
    prediction is the same ("sustantivo", "verbo" or "ambigua"). A None
    prediction counts as wrong. None if no sentence has a PP.

    Systems that never compute it (Transformers: always None) should be left
    out of this comparison by the caller.
    """
    # TODO(P4)
    raise NotImplementedError("TODO(P4): pp_attachment_accuracy")


# ----------------------------------------------------------------------
# Table (implemented): one row per system, comparison, level and metric
# ----------------------------------------------------------------------
METRICS: list[tuple[str, str, Callable[[list[Pair]], float | None]]] = [
    ("aceptacion", "precision", precision),
    ("aceptacion", "cobertura", coverage),
    ("aceptacion", "rechazo_correcto", correct_rejection_rate),
    ("aceptacion_espanol", "precision", lambda p: precision(p, "valid_spanish")),
    ("aceptacion_espanol", "cobertura", lambda p: coverage(p, "valid_spanish")),
    ("aceptacion_espanol", "rechazo_correcto", lambda p: correct_rejection_rate(p, "valid_spanish")),
    ("etiquetado", "exactitud", tagging_accuracy),
    ("funciones", "sujeto", lambda p: function_accuracy(p, "subject")),
    ("funciones", "verbo", lambda p: function_accuracy(p, "verb")),
    ("funciones", "objeto", lambda p: function_accuracy(p, "object")),
    ("estructura", "pp_adjunta", pp_attachment_accuracy),
]


# Systems that only tag: they never fill pp_adjunta, so they are not compared on it.
NO_STRUCTURE = {"transformers"}


def metric_rows(system: str, pairs: list[Pair]) -> list[dict]:
    rows = []
    groups: list[tuple[str, list[Pair]]] = [("todos", pairs)]
    groups += [(str(level), [p for p in pairs if p[0].level == level]) for level in LEVELS]
    for level, group in groups:
        if not group:
            continue
        for comparison, name, metric in METRICS:
            if comparison == "estructura" and system in NO_STRUCTURE:
                continue
            value = metric(group)
            if value is not None:
                rows.append({"sistema": system, "comparacion": comparison, "nivel": level,
                             "metrica": name, "valor": round(value, 4)})
    return rows


def compute_all() -> list[dict]:
    items = load_test_set()
    rows = []
    for system in SYSTEMS:
        if results_path(system).exists():
            rows += metric_rows(system, align(items, load_predictions(system)))
    return rows


def write_metrics(rows: list[dict]) -> None:
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["sistema", "comparacion", "nivel", "metrica", "valor"])
        writer.writeheader()
        writer.writerows(rows)


# TODO(P4): comparative tables and plots (matplotlib) in results/figures/:
#           metrics per system, per level, per category, and the length mismatches.


def main() -> None:
    rows = compute_all()
    write_metrics(rows)
    print(f"{len(rows)} filas -> {METRICS_PATH}")


if __name__ == "__main__":
    main()
