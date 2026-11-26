"""Run OUR parser on the test set and save results/parser.jsonl.  Owner: Person 2.

    python -m evaluation.run_parser

Output in the agreed format (docs/gramatica_es.md, 2.4), which Person 4 uses
for the metrics. One line per sentence, in the order of the test set; if the
parser crashes on a sentence, the line is still written with error_ejecucion.
"""

import time

from spanish.pipeline import analyze

from .formats import Prediction, TestItem, load_test_set, save_predictions


def predict(item: TestItem) -> Prediction:
    start = time.perf_counter()
    try:
        result = analyze(item.sentence)
    except NotImplementedError:
        raise  # a TODO is not a parser failure: stop and say what is missing
    except Exception as e:  # noqa: BLE001 - any crash is recorded, as the format asks
        return Prediction(item.id, "parser", accepts=None,
                          time_ms=(time.perf_counter() - start) * 1000,
                          run_error=f"{type(e).__name__}: {e}")
    elapsed = (time.perf_counter() - start) * 1000
    return Prediction(
        id=item.id,
        system="parser",
        accepts=result.accepted,
        error_type=result.error_type,
        tags=result.tags,
        subject=result.subject,
        verb=result.verb,
        object=result.object,
        pp_attachment=result.pp_attachment,
        # The agreed format writes the tree only when the sentence is accepted.
        tree=result.tree.to_bracketed(lowercase=True) if result.accepted else None,
        num_trees=1 if result.accepted else None,
        time_ms=elapsed,
    )


def main() -> None:
    items = load_test_set()
    predictions = [predict(item) for item in items]
    path = save_predictions("parser", predictions, items)
    accepted = sum(bool(p.accepts) for p in predictions)
    print(f"{len(predictions)} oraciones, {accepted} aceptadas -> {path}")


if __name__ == "__main__":
    main()
