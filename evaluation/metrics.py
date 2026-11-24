"""Metrics to compare the systems.  Owner: Person 4.

    python -m evaluation.metrics            # prints the tables for every system with results

Systems: parser (ours), spacy, transformers, llm_zero_shot, llm_few_shot.
Every system writes results/<sistema>.jsonl in the format of
evaluation/formats.py, so all metrics work the same for all of them.

PROPOSED definitions (P4 confirms them and explains them in the report).
"Positive" = the system accepts the sentence. The reference is the
`cubierta` field of the test set (what our CFG should accept):

  precision            = accepted AND covered / accepted
                         "when it accepts, how often is it right?"
  coverage (recall)    = accepted AND covered / covered
                         "how many of the sentences it should accept does it accept?"
  correct_rejection    = rejected AND NOT covered / NOT covered
                         "how many of the sentences it should reject does it reject?"
  tree_accuracy        = same_tree(predicted, expected) / covered
                         (only systems that produce our trees: parser, LLM)
  tagging_accuracy     = words with the right category / words
                         (every system: spaCy and Transformers are compared here)
  error classification = confusion matrix expected tipo_error × predicted tipo_error
                         on the sentences that are not covered

Also useful for the analysis (P1, P5): the same metrics using `gramatical`
instead of `cubierta` as the reference. A system that scores better against
`gramatical` than against `cubierta` is following its knowledge of Spanish
instead of the rules (the question of the LLM experiment).
"""

from collections import Counter

from .formats import SYSTEMS, Prediction, TestItem, load_predictions, load_test_set, results_path


def align(items: list[TestItem], predictions: list[Prediction]) -> list[tuple[TestItem, Prediction | None]]:
    """Pair each test item with its prediction (None if the system skipped it)."""
    by_id = {p.id: p for p in predictions}
    return [(item, by_id.get(item.id)) for item in items]


def precision(pairs: list[tuple[TestItem, Prediction | None]], reference: str = "covered") -> float | None:
    """accepted AND reference / accepted. None if the system accepted nothing."""
    # TODO(P4). Hint: getattr(item, reference) gives item.covered or item.grammatical.
    raise NotImplementedError("TODO(P4): precision")


def coverage(pairs: list[tuple[TestItem, Prediction | None]], reference: str = "covered") -> float | None:
    """accepted AND reference / reference."""
    # TODO(P4)
    raise NotImplementedError("TODO(P4): coverage")


def correct_rejection_rate(pairs: list[tuple[TestItem, Prediction | None]], reference: str = "covered") -> float | None:
    """rejected AND NOT reference / NOT reference."""
    # TODO(P4)
    raise NotImplementedError("TODO(P4): correct_rejection_rate")


def tree_accuracy(pairs: list[tuple[TestItem, Prediction | None]]) -> float | None:
    """Covered sentences whose predicted tree equals the expected one (spanish.tree.same_tree)."""
    # TODO(P4): a malformed predicted tree (ValueError) counts as wrong.
    raise NotImplementedError("TODO(P4): tree_accuracy")


def tagging_accuracy(pairs: list[tuple[TestItem, Prediction | None]]) -> float | None:
    """Right category per word, against the leaves of the expected tree."""
    # TODO(P4): expected categories = [leaf.label for leaf in Node.from_bracketed(item.tree).leaves()]
    #           Only covered sentences have an expected tree; decide whether to
    #           label the others too (e.g. an "categorias" field in the test set).
    raise NotImplementedError("TODO(P4): tagging_accuracy")


def error_confusion(pairs: list[tuple[TestItem, Prediction | None]]) -> Counter:
    """Counter[(expected tipo_error, predicted tipo_error)] on non-covered sentences."""
    # TODO(P4)
    raise NotImplementedError("TODO(P4): error_confusion")


def by_level(pairs, metric, **kwargs) -> dict[str, float | None]:
    """The same metric split by level: {"simple": 0.9, "intermedia": ..., "compleja": ...}."""
    # TODO(P4)
    raise NotImplementedError("TODO(P4): by_level")


def summary_table() -> list[dict]:
    """One row per system that has a results file. Base for the report tables."""
    items = load_test_set()
    rows = []
    for system in SYSTEMS:
        if not results_path(system).exists():
            continue
        pairs = align(items, load_predictions(system))
        rows.append({
            "sistema": system,
            "precision": precision(pairs),
            "cobertura": coverage(pairs),
            "rechazo_correcto": correct_rejection_rate(pairs),
            "arbol_exacto": tree_accuracy(pairs),
            "categorias": tagging_accuracy(pairs),
        })
    return rows


# TODO(P4): plots (matplotlib) saved to results/figures/: metrics per system,
#           metrics per level, error confusion. Maybe in a notebook of its own.


def main() -> None:
    for row in summary_table():
        print(row)


if __name__ == "__main__":
    main()
