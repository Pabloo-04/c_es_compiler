"""Run OUR parser on the test set and save results/parser.jsonl.  Owner: Person 2.

    python -m evaluation.run_parser

The output is what Person 4 uses for the metrics. Same format as the other
systems (evaluation/formats.py).
"""

from spanish.pipeline import analyze

from .formats import Prediction, load_test_set, save_predictions


def predict(item) -> Prediction:
    result = analyze(item.sentence)
    return Prediction(
        id=item.id,
        system="parser",
        accepted=result.accepted,
        # The tree is saved even when agreement fails: it shows the parse was fine.
        tree=result.tree.to_bracketed() if result.tree is not None else None,
        categories=[leaf.label for leaf in result.tree.leaves()] if result.tree else None,
        error_type=result.error_type,
        detail="; ".join(str(e) for e in result.errors),
    )


def main() -> None:
    items = load_test_set()
    predictions = [predict(item) for item in items]
    path = save_predictions("parser", predictions)
    accepted = sum(p.accepted for p in predictions)
    print(f"{len(predictions)} oraciones, {accepted} aceptadas -> {path}")


if __name__ == "__main__":
    main()
