"""Confusion matrices and classification reports for the experiment notebooks.

Generic over the results format (evaluation/formats.py), so the same helpers
work for spaCy, Transformers, the LLM and our parser:

  - Tagging (every system): word-level confusion matrix (expected category ×
    predicted category) and classification report per category (precision,
    recall, F1, support, plus accuracy and macro/weighted averages).
  - Acceptance (systems that decide: parser and LLM): 2×2 confusion matrix of
    `acepta` against `en_gramatica` (or `espanol_valido`) and its metrics.
  - Syntactic functions: accuracy of sujeto, verbo and objeto.

Labels in the tables are in Spanish, like the report. Uses pandas,
scikit-learn and matplotlib (requirements-experiments.txt).
"""

from pathlib import Path

import pandas as pd

from evaluation.formats import CATEGORIES, Prediction, TestItem

REFERENCES = {"in_grammar": "en_gramatica", "valid_spanish": "espanol_valido"}


# ----------------------------------------------------------------------
# Tagging
# ----------------------------------------------------------------------
def tag_pairs(items: list[TestItem], predictions: list[Prediction]) -> tuple[list[str], list[str], list[int]]:
    """Word-aligned (expected, predicted) categories.

    Sentences with no tags or a different number of words cannot be aligned
    word by word: they are left out and their ids returned apart, as
    docs/gramatica_es.md 2.7 says ("se reporta aparte").
    """
    by_id = {p.id: p for p in predictions}
    y_true, y_pred, skipped = [], [], []
    for item in items:
        pred = by_id.get(item.id)
        if pred is None or pred.tags is None or len(pred.tags) != len(item.tags):
            skipped.append(item.id)
            continue
        y_true += [category for _, category in item.tags]
        y_pred += [category for _, category in pred.tags]
    return y_true, y_pred, skipped


def _labels(y_true: list[str], y_pred: list[str]) -> list[str]:
    """Agreed categories in their canonical order, then any unexpected label."""
    present = set(y_true) | set(y_pred)
    return [c for c in CATEGORIES if c in present] + sorted(present - set(CATEGORIES))


def tag_confusion(y_true: list[str], y_pred: list[str]) -> pd.DataFrame:
    """Rows = expected category, columns = predicted category, cells = words."""
    from sklearn.metrics import confusion_matrix

    labels = _labels(y_true, y_pred)
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    return pd.DataFrame(
        matrix,
        index=pd.Index(labels, name="esperado"),
        columns=pd.Index(labels, name="predicho"),
    )


def tag_report(y_true: list[str], y_pred: list[str]) -> pd.DataFrame:
    """Classification report per category, plus exactitud and macro/weighted averages.

    A category that the system never predicts gets precision 0 (zero_division=0),
    so the average does not hide it.
    """
    from sklearn.metrics import classification_report

    labels = _labels(y_true, y_pred)
    report = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
    accuracy = report.pop("accuracy", None)
    if accuracy is None:  # sklearn omits it when labels is a subset; recompute
        accuracy = sum(t == p for t, p in zip(y_true, y_pred)) / len(y_true) if y_true else 0.0
    table = pd.DataFrame(report).T.rename(columns={
        "precision": "precision", "recall": "cobertura", "f1-score": "f1", "support": "soporte",
    }).rename(index={"macro avg": "promedio macro", "weighted avg": "promedio ponderado"})
    # With every present label listed, the micro average equals the accuracy: keep only "exactitud".
    table = table.drop(index="micro avg", errors="ignore")
    table.loc["exactitud"] = [None, None, accuracy, len(y_true)]
    table["soporte"] = table["soporte"].astype(int)
    return table


# ----------------------------------------------------------------------
# Acceptance (parser and LLM)
# ----------------------------------------------------------------------
def acceptance_confusion(items: list[TestItem], predictions: list[Prediction],
                         reference: str = "in_grammar") -> pd.DataFrame:
    """2×2 matrix of `acepta` against the reference. Predictions with acepta
    = null (no decision, or an invalid LLM answer) are left out."""
    by_id = {p.id: p for p in predictions}
    counts = {("si", "acepta"): 0, ("si", "rechaza"): 0, ("no", "acepta"): 0, ("no", "rechaza"): 0}
    for item in items:
        pred = by_id.get(item.id)
        if pred is None or pred.accepts is None:
            continue
        expected = "si" if getattr(item, reference) else "no"
        counts[(expected, "acepta" if pred.accepts else "rechaza")] += 1
    name = REFERENCES[reference]
    return pd.DataFrame(
        [[counts[("si", "acepta")], counts[("si", "rechaza")]],
         [counts[("no", "acepta")], counts[("no", "rechaza")]]],
        index=pd.Index(["si", "no"], name=f"{name} (esperado)"),
        columns=pd.Index(["acepta", "rechaza"], name="sistema"),
    )


def acceptance_report(matrix: pd.DataFrame) -> pd.Series:
    """Metrics of docs/gramatica_es.md 2.7 (a) from the 2×2 matrix. None when undefined."""
    tp, fn = matrix.loc["si", "acepta"], matrix.loc["si", "rechaza"]
    fp, tn = matrix.loc["no", "acepta"], matrix.loc["no", "rechaza"]

    def ratio(a, b):
        return None if b == 0 else a / b

    precision, recall = ratio(tp, tp + fp), ratio(tp, tp + fn)
    f1 = None if not precision or not recall else 2 * precision * recall / (precision + recall)
    return pd.Series({
        "VP": tp, "FP": fp, "FN": fn, "VN": tn,
        "precision": precision,
        "cobertura": recall,
        "f1": f1,
        "rechazo_correcto": ratio(tn, tn + fp),
        "exactitud": ratio(tp + tn, tp + tn + fp + fn),
    })


# ----------------------------------------------------------------------
# Syntactic functions
# ----------------------------------------------------------------------
def function_report(items: list[TestItem], predictions: list[Prediction]) -> pd.DataFrame:
    """Exact-match accuracy of sujeto, verbo and objeto. None values are left out."""
    by_id = {p.id: p for p in predictions}
    rows = []
    for field, name in (("subject", "sujeto"), ("verb", "verbo"), ("object", "objeto")):
        pairs = [(getattr(i, field), getattr(by_id[i.id], field)) for i in items
                 if i.id in by_id and getattr(by_id[i.id], field) is not None]
        right = sum(expected == got for expected, got in pairs)
        rows.append({"funcion": name, "aciertos": right, "total": len(pairs),
                     "exactitud": right / len(pairs) if pairs else None})
    return pd.DataFrame(rows).set_index("funcion")


# ----------------------------------------------------------------------
# Plot
# ----------------------------------------------------------------------
def plot_confusion(matrix: pd.DataFrame, title: str, path: Path | str | None = None):
    """Heatmap with the count in each cell; saved to `path` if given. Returns the figure."""
    import matplotlib.pyplot as plt

    size = max(4.0, 0.6 * len(matrix.columns) + 2)
    fig, ax = plt.subplots(figsize=(size, size * 0.85))
    image = ax.imshow(matrix.values, cmap="Blues")
    ax.set_xticks(range(len(matrix.columns)), matrix.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(matrix.index)), matrix.index)
    ax.set_xlabel(matrix.columns.name or "")
    ax.set_ylabel(matrix.index.name or "")
    ax.set_title(title)
    limit = matrix.values.max() / 2 if matrix.values.size else 0
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix.iat[i, j]
            ax.text(j, i, value, ha="center", va="center",
                    color="white" if value > limit else "black")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    if path is not None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=150)
    return fig


# ----------------------------------------------------------------------
# PP attachment (docs/gramatica_es.md 2.7 d)
# ----------------------------------------------------------------------
PP_VALUES = ["sustantivo", "verbo", "ambigua"]
NO_ANSWER = "sin respuesta"


def pp_attachment_report(items: list[TestItem], predictions: list[Prediction]) -> tuple[pd.DataFrame, pd.Series]:
    """Confusion matrix (expected × predicted) and summary, on sentences with a PP.

    A prediction of None counts as "sin respuesta" (the system did not decide,
    or did not see the PP), so it is wrong, not excluded: otherwise a system
    could look better by not answering.
    """
    by_id = {p.id: p for p in predictions}
    rows = [(item.pp_attachment, (by_id[item.id].pp_attachment if item.id in by_id else None) or NO_ANSWER)
            for item in items if item.pp_attachment is not None]
    columns = PP_VALUES + [NO_ANSWER]
    matrix = pd.DataFrame(0, index=pd.Index(PP_VALUES, name="esperado"),
                          columns=pd.Index(columns, name="predicho"))
    for expected, got in rows:
        matrix.loc[expected, got if got in columns else NO_ANSWER] += 1
    ambiguous = [got for expected, got in rows if expected == "ambigua"]
    summary = pd.Series({
        "oraciones_con_pp": len(rows),
        "aciertos": sum(e == g for e, g in rows),
        "exactitud": sum(e == g for e, g in rows) / len(rows) if rows else None,
        "ambiguas": len(ambiguous),
        "ambiguas_detectadas": sum(g == "ambigua" for g in ambiguous),
        "sin_respuesta": sum(g == NO_ANSWER for _, g in rows),
    })
    return matrix, summary
