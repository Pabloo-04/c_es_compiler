"""Metrics to compare the systems.  Owner: Person 4.

    python -m evaluation.metrics          # results/metrics.csv, results/metricas.md,
                                          # results/tablas/*.tex and results/figures/*.png

Definitions: docs/gramatica_es.md, section 2.7. Each system takes part in the
comparisons it has data for (None values are excluded):

  a) Acceptance (parser, Transformers, LLM): `acepta` against `en_gramatica`,
     and also against `espanol_valido`. The positive class is "accepts".
         precision          = TP / (TP + FP)
         coverage (recall)  = TP / (TP + FN)
         correct rejection  = TN / (TN + FP)
         accuracy           = (TP + TN) / total;  F1 = harmonic mean of precision and coverage
         error type         = right tipo_error / correctly rejected sentences
                              (only systems that give a tipo_error: parser and LLM)
     A prediction with acepta = null is left out (spaCy never decides), EXCEPT
     when the system crashed on that sentence (error_ejecucion, e.g. an LLM
     answer that is not JSON): that counts as a wrong answer (2.6), otherwise
     a system could look better by failing.
  b) Tagging (every system): tags word by word against `etiquetas`.
         accuracy = right words / total words, over the sentences with the same
         number of words; precision and recall per category; the sentences
         with a different number of words are counted apart.
  c) Syntactic functions: `sujeto`, `verbo`, `objeto`, exact match.
  d) PP attachment (parser, spaCy, LLM): `pp_adjunta` against the test set,
     only on sentences with a PP; a None prediction counts as wrong. Also how
     many of the `ambigua` sentences the system marked as `ambigua`.
  e) Cost: mean processing time per sentence (tiempo_ms).

Output: results/metrics.csv with the columns
    sistema,comparacion,nivel,metrica,valor
where nivel is 1, 2, 3 or "todos". The tables for the report are built from
those rows (results/metricas.md and results/tablas/*.tex) and the plots are
in evaluation/plots.py.
"""

import csv
import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path

from .formats import (
    CATEGORIES,
    LEVELS,
    METRICS_PATH,
    PP_ATTACHMENTS,
    RESULTS_DIR,
    SYSTEMS,
    Prediction,
    TestItem,
    load_predictions,
    load_test_set,
    results_path,
)

Pair = tuple[TestItem, Prediction]

REFERENCES = ("in_grammar", "valid_spanish")


def align(items: list[TestItem], predictions: list[Prediction]) -> list[Pair]:
    """Pair each test item with its prediction (same id). Missing ids raise."""
    by_id = {p.id: p for p in predictions}
    missing = [i.id for i in items if i.id not in by_id]
    if missing:
        shown = ", ".join(map(str, missing[:5])) + (f"… ({len(missing)} en total)" if len(missing) > 5 else "")
        raise ValueError(f"faltan resultados para los ids {shown}")
    return [(item, by_id[item.id]) for item in items]


def _ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


# ----------------------------------------------------------------------
# a) Acceptance
# ----------------------------------------------------------------------
def _expected(item: TestItem, reference: str) -> bool:
    if reference not in REFERENCES:
        raise ValueError(f"referencia desconocida {reference!r}; usa una de {REFERENCES}")
    return getattr(item, reference)


def _decision(pred: Prediction, expected: bool) -> bool | None:
    """What the system answered: True/False, None if it does not decide.
    A crash counts as the wrong answer."""
    if pred.accepts is not None:
        return pred.accepts
    if pred.run_error:
        return not expected
    return None


def confusion(pairs: list[Pair], reference: str = "in_grammar") -> dict[str, int]:
    """{"TP": .., "FP": .., "FN": .., "TN": ..} of `acepta` against the reference.

    reference: "in_grammar" (en_gramatica) or "valid_spanish" (espanol_valido).
    Predictions with accepts None (the system does not decide) are excluded.
    """
    counts = {"TP": 0, "FP": 0, "FN": 0, "TN": 0}
    for item, pred in pairs:
        expected = _expected(item, reference)
        accepts = _decision(pred, expected)
        if accepts is None:
            continue
        key = ("T" if accepts == expected else "F") + ("P" if accepts else "N")
        counts[key] += 1
    return counts


def precision(pairs: list[Pair], reference: str = "in_grammar") -> float | None:
    """TP / (TP + FP). None if the denominator is 0."""
    c = confusion(pairs, reference)
    return _ratio(c["TP"], c["TP"] + c["FP"])


def coverage(pairs: list[Pair], reference: str = "in_grammar") -> float | None:
    """TP / (TP + FN)."""
    c = confusion(pairs, reference)
    return _ratio(c["TP"], c["TP"] + c["FN"])


def correct_rejection_rate(pairs: list[Pair], reference: str = "in_grammar") -> float | None:
    """TN / (TN + FP)."""
    c = confusion(pairs, reference)
    return _ratio(c["TN"], c["TN"] + c["FP"])


def acceptance_accuracy(pairs: list[Pair], reference: str = "in_grammar") -> float | None:
    """(TP + TN) / every sentence the system decided on."""
    c = confusion(pairs, reference)
    return _ratio(c["TP"] + c["TN"], sum(c.values()))


def f1(pairs: list[Pair], reference: str = "in_grammar") -> float | None:
    p, r = precision(pairs, reference), coverage(pairs, reference)
    if p is None or r is None or p + r == 0:
        return None
    return 2 * p * r / (p + r)


def error_type_accuracy(pairs: list[Pair]) -> float | None:
    """Of the sentences correctly rejected (en_gramatica = no and acepta = false),
    the share with the expected tipo_error ("sintactico" or "concordancia")."""
    rejected = [(item, pred) for item, pred in pairs if not item.in_grammar and pred.accepts is False]
    return _ratio(sum(pred.error_type == item.error_type for item, pred in rejected), len(rejected))


def error_type_confusion(pairs: list[Pair]) -> Counter:
    """Counter[(expected tipo_error, what the system did)] on the sentences
    with en_gramatica = no. The system side is its tipo_error, or "acepta",
    "sin_tipo" (rejected without a type) or "sin_decision"."""
    result = Counter()
    for item, pred in pairs:
        if item.in_grammar:
            continue
        if pred.accepts is None:
            got = "sin_decision"
        elif pred.accepts:
            got = "acepta"
        else:
            got = pred.error_type or "sin_tipo"
        result[(item.error_type, got)] += 1
    return result


# ----------------------------------------------------------------------
# b) Tagging
# ----------------------------------------------------------------------
def _comparable(pairs: list[Pair]) -> list[Pair]:
    """Pairs whose tags can be compared word by word."""
    return [(item, pred) for item, pred in pairs
            if pred.tags is not None and len(pred.tags) == len(item.tags)]


def tagging_accuracy(pairs: list[Pair]) -> float | None:
    """Right words / total words, over the sentences with the same number of
    words as expected. None if no sentence can be compared."""
    right = total = 0
    for item, pred in _comparable(pairs):
        right += sum(expected == got[1] for (_, expected), got in zip(item.tags, pred.tags))
        total += len(item.tags)
    return _ratio(right, total)


def length_mismatches(pairs: list[Pair]) -> list[int]:
    """ids where the system produced a different number of words (reported apart)."""
    return [item.id for item, pred in pairs
            if pred.tags is not None and len(pred.tags) != len(item.tags)]


def tag_confusion(pairs: list[Pair]) -> Counter:
    """Counter[(expected category, predicted category)] over the comparable words."""
    result = Counter()
    for item, pred in _comparable(pairs):
        for (_, expected), (_, got) in zip(item.tags, pred.tags):
            result[(expected, got)] += 1
    return result


def per_category(pairs: list[Pair]) -> dict[str, dict[str, float | None]]:
    """{"Adj": {"precision": .., "cobertura": ..}, ...} for every category."""
    matrix = tag_confusion(pairs)
    result = {}
    for category in CATEGORIES:
        right = matrix[(category, category)]
        predicted = sum(n for (_, got), n in matrix.items() if got == category)
        expected = sum(n for (exp, _), n in matrix.items() if exp == category)
        result[category] = {"precision": _ratio(right, predicted), "cobertura": _ratio(right, expected)}
    return result


# ----------------------------------------------------------------------
# c) Syntactic functions
# ----------------------------------------------------------------------
def function_accuracy(pairs: list[Pair], field: str) -> float | None:
    """field: "subject", "verb" or "object". Exact match; None predictions excluded."""
    compared = [(getattr(item, field), getattr(pred, field)) for item, pred in pairs
                if getattr(pred, field) is not None]
    return _ratio(sum(expected == got.lower() for expected, got in compared), len(compared))


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
    with_pp = [(item, pred) for item, pred in pairs if item.pp_attachment is not None]
    return _ratio(sum(pred.pp_attachment == item.pp_attachment for item, pred in with_pp), len(with_pp))


def ambiguity_detection(pairs: list[Pair]) -> float | None:
    """Of the sentences whose PP is `ambigua`, the share the system marked `ambigua`."""
    ambiguous = [pred for item, pred in pairs if item.pp_attachment == "ambigua"]
    return _ratio(sum(pred.pp_attachment == "ambigua" for pred in ambiguous), len(ambiguous))


def pp_confusion(pairs: list[Pair]) -> Counter:
    """Counter[(expected, predicted)] on sentences with a PP; None -> "sin_respuesta"."""
    return Counter((item.pp_attachment, pred.pp_attachment or "sin_respuesta")
                   for item, pred in pairs if item.pp_attachment is not None)


# ----------------------------------------------------------------------
# e) Cost
# ----------------------------------------------------------------------
def mean_time_ms(pairs: list[Pair]) -> float | None:
    times = [pred.time_ms for _, pred in pairs if pred.time_ms]
    return _ratio(sum(times), len(times))


def run_errors(pairs: list[Pair]) -> int:
    return sum(bool(pred.run_error) for _, pred in pairs)


# ----------------------------------------------------------------------
# Table: one row per system, comparison, level and metric
# ----------------------------------------------------------------------
METRICS: list[tuple[str, str, Callable[[list[Pair]], float | None]]] = [
    ("aceptacion", "precision", precision),
    ("aceptacion", "cobertura", coverage),
    ("aceptacion", "rechazo_correcto", correct_rejection_rate),
    ("aceptacion", "exactitud", acceptance_accuracy),
    ("aceptacion", "f1", f1),
    ("aceptacion", "tipo_error", error_type_accuracy),
    ("aceptacion_espanol", "precision", lambda p: precision(p, "valid_spanish")),
    ("aceptacion_espanol", "cobertura", lambda p: coverage(p, "valid_spanish")),
    ("aceptacion_espanol", "rechazo_correcto", lambda p: correct_rejection_rate(p, "valid_spanish")),
    ("aceptacion_espanol", "exactitud", lambda p: acceptance_accuracy(p, "valid_spanish")),
    ("aceptacion_espanol", "f1", lambda p: f1(p, "valid_spanish")),
    ("etiquetado", "exactitud", tagging_accuracy),
    ("etiquetado", "oraciones_distinto_largo", lambda p: len(length_mismatches(p))),
    ("funciones", "sujeto", lambda p: function_accuracy(p, "subject")),
    ("funciones", "verbo", lambda p: function_accuracy(p, "verb")),
    ("funciones", "objeto", lambda p: function_accuracy(p, "object")),
    ("estructura", "pp_adjunta", pp_attachment_accuracy),
    ("estructura", "ambiguas_detectadas", ambiguity_detection),
    ("costo", "tiempo_ms_promedio", mean_time_ms),
    ("costo", "errores_ejecucion", run_errors),
]

# Systems that only tag: they never fill pp_adjunta, so they are not compared on it.
NO_STRUCTURE = {"transformers"}
# Systems that never say WHY a sentence is wrong (tipo_error always null).
NO_ERROR_TYPE = {"spacy", "transformers"}


def _decides(pairs: list[Pair]) -> bool:
    return any(pred.accepts is not None for _, pred in pairs)


def metric_rows(system: str, pairs: list[Pair]) -> list[dict]:
    rows = []
    decides = _decides(pairs)
    groups: list[tuple[str, list[Pair]]] = [("todos", pairs)]
    groups += [(str(level), [p for p in pairs if p[0].level == level]) for level in LEVELS]
    for level, group in groups:
        if not group:
            continue
        for comparison, name, metric in METRICS:
            if comparison.startswith("aceptacion") and not decides:
                continue
            if name == "tipo_error" and system in NO_ERROR_TYPE:
                continue
            if comparison == "estructura" and system in NO_STRUCTURE:
                continue
            value = metric(group)
            if value is not None:
                rows.append({"sistema": system, "comparacion": comparison, "nivel": level,
                             "metrica": name, "valor": round(value, 4)})
        if level == "todos":
            for category, values in per_category(group).items():
                for name, value in values.items():
                    if value is not None:
                        rows.append({"sistema": system, "comparacion": "etiquetado_categoria",
                                     "nivel": level, "metrica": f"{name}_{category}",
                                     "valor": round(value, 4)})
    return rows


def load_all_pairs(items: list[TestItem] | None = None, warn=print) -> dict[str, list[Pair]]:
    """{system: pairs} for every system whose results file matches the test set.

    A results file from an older version of the test set (missing ids) is
    skipped with a warning instead of stopping everything: that system has to
    be run again.
    """
    items = load_test_set() if items is None else items
    all_pairs = {}
    for system in SYSTEMS:
        if not results_path(system).exists():
            continue
        try:
            all_pairs[system] = align(items, load_predictions(system))
        except ValueError as e:
            warn(f"AVISO: se omite {system}: {e}. Hay que volver a correrlo con el set actual.")
    return all_pairs


def compute_all(all_pairs: dict[str, list[Pair]] | None = None) -> list[dict]:
    all_pairs = load_all_pairs() if all_pairs is None else all_pairs
    rows = []
    for system, pairs in all_pairs.items():
        rows += metric_rows(system, pairs)
    return rows


def write_metrics(rows: list[dict]) -> None:
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["sistema", "comparacion", "nivel", "metrica", "valor"])
        writer.writeheader()
        writer.writerows(rows)


# ----------------------------------------------------------------------
# Tables for the report (Markdown and LaTeX), built from the metric rows
# ----------------------------------------------------------------------
SYSTEM_NAMES = {
    "parser": "Parser propio",
    "spacy": "spaCy",
    "transformers": "Transformers",
    "llm_zero": "LLM zero-shot",
    "llm_few": "LLM few-shot",
}
LEVEL_NAMES = {"1": "Nivel 1", "2": "Nivel 2", "3": "Nivel 3", "todos": "Todos"}


def value(rows: list[dict], system: str, comparison: str, metric: str, level: str = "todos"):
    for row in rows:
        if (row["sistema"], row["comparacion"], row["metrica"], row["nivel"]) == (system, comparison, metric, level):
            return row["valor"]
    return None


def _systems(rows: list[dict]) -> list[str]:
    present = {row["sistema"] for row in rows}
    return [s for s in SYSTEMS if s in present]


def _metric_table(rows, comparison, metrics: dict[str, str], level="todos") -> tuple[list[str], list[list]]:
    header = ["Sistema", *metrics.values()]
    body = []
    for system in _systems(rows):
        values = [value(rows, system, comparison, m, level) for m in metrics]
        if any(v is not None for v in values):
            body.append([SYSTEM_NAMES[system], *values])
    return header, body


def _level_table(rows, comparison, metric) -> tuple[list[str], list[list]]:
    header = ["Sistema", *(LEVEL_NAMES[lv] for lv in ("1", "2", "3", "todos"))]
    body = []
    for system in _systems(rows):
        values = [value(rows, system, comparison, metric, lv) for lv in ("1", "2", "3", "todos")]
        if any(v is not None for v in values):
            body.append([SYSTEM_NAMES[system], *values])
    return header, body


def test_set_table(items: list[TestItem]) -> tuple[list[str], list[list]]:
    header = ["Nivel", "Oraciones", "En la gramática", "Fuera de la gramática",
              "Válidas fuera de la gramática", "Error sintáctico", "Error de concordancia", "Con PP"]
    body = []
    for level in (*LEVELS, None):
        subset = [i for i in items if level is None or i.level == level]
        body.append([
            LEVEL_NAMES[str(level) if level else "todos"], len(subset),
            sum(i.in_grammar for i in subset), sum(not i.in_grammar for i in subset),
            sum(i.valid_spanish and not i.in_grammar for i in subset),
            sum(i.error_type == "sintactico" for i in subset),
            sum(i.error_type == "concordancia" for i in subset),
            sum(i.pp_attachment is not None for i in subset),
        ])
    return header, body


def phenomena_table(items: list[TestItem]) -> tuple[list[str], list[list]]:
    from .formats import PHENOMENA

    header = ["Fenómeno", "Nivel 1", "Nivel 2", "Nivel 3", "Total"]
    body = []
    for phenomenon in PHENOMENA:
        counts = [sum(phenomenon in i.phenomena for i in items if i.level == lv) for lv in LEVELS]
        body.append([phenomenon.replace("_", " "), *counts, sum(counts)])
    return header, body


def category_table(rows) -> tuple[list[str], list[list]]:
    systems = _systems(rows)
    header = ["Categoría", *(SYSTEM_NAMES[s] for s in systems)]
    body = []
    for category in CATEGORIES:
        values = [value(rows, s, "etiquetado_categoria", f"cobertura_{category}") for s in systems]
        if any(v is not None for v in values):
            body.append([category, *values])
    return header, body


def error_type_table(all_pairs) -> tuple[list[str], list[list]]:
    columns = ["acepta", "sintactico", "concordancia", "sin_tipo", "sin_decision"]
    header = ["Sistema", "Esperado", *(c.replace("_", " ") for c in columns)]
    body = []
    for system, pairs in all_pairs.items():
        if not _decides(pairs):
            continue
        matrix = error_type_confusion(pairs)
        for expected in ("sintactico", "concordancia"):
            body.append([SYSTEM_NAMES[system], expected, *(matrix[(expected, c)] for c in columns)])
    return header, body


def pp_table(all_pairs) -> tuple[list[str], list[list]]:
    columns = [*PP_ATTACHMENTS, "sin_respuesta"]
    header = ["Sistema", "Esperado", *(c.replace("_", " ") for c in columns)]
    body = []
    for system, pairs in all_pairs.items():
        if system in NO_STRUCTURE:
            continue
        matrix = pp_confusion(pairs)
        for expected in PP_ATTACHMENTS:
            body.append([SYSTEM_NAMES[system], expected, *(matrix[(expected, c)] for c in columns)])
    return header, body


ACCEPTANCE_METRICS = {"precision": "Precisión", "cobertura": "Cobertura",
                      "rechazo_correcto": "Rechazo correcto", "exactitud": "Exactitud", "f1": "F1"}


def build_tables(items: list[TestItem], rows: list[dict], all_pairs) -> dict[str, tuple[str, list[str], list[list]]]:
    """name -> (title, header, body). Same content for Markdown and LaTeX."""
    return {
        "set_de_prueba": ("Composición del conjunto de prueba", *test_set_table(items)),
        "fenomenos": ("Fenómenos por nivel (una oración puede tener varios)", *phenomena_table(items)),
        "aceptacion": ("Aceptación contra en_gramatica (las reglas)",
                       *_metric_table(rows, "aceptacion", {**ACCEPTANCE_METRICS, "tipo_error": "Tipo de error"})),
        "aceptacion_espanol": ("Aceptación contra espanol_valido (el español)",
                               *_metric_table(rows, "aceptacion_espanol", ACCEPTANCE_METRICS)),
        "exactitud_aceptacion_por_nivel": ("Exactitud de la aceptación por nivel (contra en_gramatica)",
                                           *_level_table(rows, "aceptacion", "exactitud")),
        "tipo_error": ("Tipo de error esperado frente a la respuesta (oraciones fuera de la gramática)",
                       *error_type_table(all_pairs)),
        "etiquetado": ("Etiquetado palabra por palabra",
                       *_metric_table(rows, "etiquetado", {"exactitud": "Etiquetas", "oraciones_distinto_largo": "Distinto largo"})),
        "funciones": ("Funciones sintácticas (coincidencia exacta)",
                      *_metric_table(rows, "funciones", {"sujeto": "Sujeto", "verbo": "Verbo", "objeto": "Objeto"})),
        "etiquetado_por_nivel": ("Exactitud del etiquetado por nivel", *_level_table(rows, "etiquetado", "exactitud")),
        "etiquetado_categoria": ("Cobertura (recall) del etiquetado por categoría", *category_table(rows)),
        "pp_adjunta": ("Unión de la PP", *_metric_table(rows, "estructura", {
            "pp_adjunta": "Exactitud", "ambiguas_detectadas": "Ambiguas detectadas"})),
        "pp_confusion": ("Unión de la PP: esperado frente a predicho", *pp_table(all_pairs)),
        "costo": ("Costo", *_metric_table(rows, "costo", {
            "tiempo_ms_promedio": "Tiempo medio (ms)", "errores_ejecucion": "Errores de ejecución"})),
    }


def fmt(v) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.2f}" if abs(v) < 10 else f"{v:.1f}"
    return str(v)


def markdown_table(header: list[str], body: list[list]) -> str:
    if not body:
        return "_(sin datos)_"
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in body]
    return "\n".join(lines)


def latex_table(header: list[str], body: list[list]) -> str:
    """booktabs tabular, ready for \\input in the report."""
    if not body:
        return "\\pendiente{sin datos}\n"

    def tex(v) -> str:
        return fmt(v).replace("_", r"\_").replace("—", "---").replace("%", r"\%")

    lines = [r"\begin{tabular}{l" + "r" * (len(header) - 1) + "}", r"\toprule",
             " & ".join(tex(h) for h in header) + r" \\", r"\midrule"]
    lines += [" & ".join(tex(v) for v in row) + r" \\" for row in body]
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines) + "\n"


def write_tables(tables: dict, directory: Path = RESULTS_DIR) -> list[Path]:
    (directory / "tablas").mkdir(parents=True, exist_ok=True)
    paths = []
    parts = ["# Resultados de las métricas\n", "Generado con `python -m evaluation.metrics`. "
             "Definiciones: `docs/gramatica_es.md`, sección 2.7.\n"]
    for name, (title, header, body) in tables.items():
        parts.append(f"## {title}\n\n{markdown_table(header, body)}\n")
        path = directory / "tablas" / f"{name}.tex"
        path.write_text(latex_table(header, body), encoding="utf-8")
        paths.append(path)
    md = directory / "metricas.md"
    md.write_text("\n".join(parts), encoding="utf-8")
    return [md, *paths]


def main() -> None:
    items = load_test_set()
    all_pairs = load_all_pairs(items)
    rows = compute_all(all_pairs)
    write_metrics(rows)
    print(f"{len(rows)} filas -> {METRICS_PATH}")
    tables = build_tables(items, rows, all_pairs)
    paths = write_tables(tables)
    print(f"tablas -> {paths[0]} y {paths[1].parent}/")
    for name in ("aceptacion", "aceptacion_espanol", "etiquetado", "funciones", "pp_adjunta", "costo"):
        title, header, body = tables[name]
        print(f"\n## {title}\n{markdown_table(header, body)}")
    try:
        from .plots import save_all
    except ImportError as e:  # matplotlib is in requirements-experiments.txt
        print(f"\nSin gráficas ({e}). Instalar: pip install -r requirements-experiments.txt", file=sys.stderr)
        return
    for path in save_all(items, rows, all_pairs):
        print("->", path)


if __name__ == "__main__":
    main()
