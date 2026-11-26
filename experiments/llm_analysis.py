"""Analysis of the LLM experiment.  Owner: Person 5.

The metrics shared by every system (precision, coverage, correct rejection,
tagging, functions, PP attachment) are in evaluation/metrics.py (P4) and
experiments/reports.py. This module answers the questions that are specific to
the LLM, with numbers:

  (a) Does it follow the rules or drift towards its knowledge of Spanish?
      - coincide_reglas / coincide_espanol: decisions that match en_gramatica /
        espanol_valido. More with espanol_valido = it follows Spanish, not us.
      - desviacion: correct Spanish that our grammar does NOT generate, accepted.
      - arbol_en_gramatica: its trees use only the shapes of TREE_SHAPES.
      - arbol_igual_parser: its tree is the one our parser builds.
  (b) Where does it get it right and where does it fail?  -> by_group() by
      level and by phenomenon, per_sentence().
  (c) Does few-shot improve on zero-shot?  -> summary() of both systems.
  Format and cost: answer_format(), cost_from_log().

Plain lists and dicts (no pandas), so the tests run without the notebook
dependencies; the notebook turns them into tables.
"""

from collections import defaultdict
from statistics import mean

from evaluation.formats import Prediction, TestItem
from spanish.grammar import tree_shape_errors
from spanish.tree import Node, same_tree

from . import prompts


def _ratio(hits: int, total: int) -> float | None:
    return hits / total if total else None


def tree_follows_grammar(tree: str | None) -> bool:
    """True if the tree parses and every node has the children TREE_SHAPES allows."""
    if not tree:
        return False
    try:
        return tree_shape_errors(Node.from_bracketed(tree)) == []
    except ValueError:
        return False


def _same_tree(a: str | None, b: str | None) -> bool:
    try:
        return a is not None and b is not None and same_tree(a, b)
    except ValueError:
        return False


def summary(items: list[TestItem], predictions: list[Prediction],
            parser: list[Prediction] | None = None) -> dict:
    """One row of numbers for one system (llm_zero or llm_few).

    parser: results/parser.jsonl, to compare trees with the ones our grammar
    really builds (the test set has no expected trees).
    """
    by_id = {p.id: p for p in predictions}
    pairs = [(i, by_id[i.id]) for i in items if i.id in by_id]
    decided = [(i, p) for i, p in pairs if p.accepts is not None]
    drift_set = [(i, p) for i, p in decided if not i.in_grammar and i.valid_spanish]
    wrong_spanish = [(i, p) for i, p in decided if not i.valid_spanish]
    rejected_ok = [(i, p) for i, p in decided if not i.in_grammar and p.accepts is False]
    with_tree = [p for _, p in decided if p.accepts and p.tree]
    parser_trees = {p.id: p.tree for p in parser or [] if p.accepts and p.tree}
    comparable = [(i, p) for i, p in decided if p.accepts and i.id in parser_trees]
    return {
        "oraciones": len(pairs),
        "sin_json": sum(p.run_error == "respuesta_no_json" for _, p in pairs),
        "coincide_reglas": _ratio(sum(p.accepts == i.in_grammar for i, p in decided), len(decided)),
        "coincide_espanol": _ratio(sum(p.accepts == i.valid_spanish for i, p in decided), len(decided)),
        "desviacion": _ratio(sum(bool(p.accepts) for _, p in drift_set), len(drift_set)),
        "acepta_agramaticales": _ratio(sum(bool(p.accepts) for _, p in wrong_spanish), len(wrong_spanish)),
        "tipo_error_correcto": _ratio(sum(p.error_type == i.error_type for i, p in rejected_ok), len(rejected_ok)),
        "arbol_en_gramatica": _ratio(sum(tree_follows_grammar(p.tree) for p in with_tree), len(with_tree)),
        "arbol_igual_parser": _ratio(
            sum(_same_tree(p.tree, parser_trees[i.id]) for i, p in comparable), len(comparable)
        ) if parser is not None else None,
    }


def by_group(items: list[TestItem], predictions: list[Prediction], key: str = "level",
             parser: list[Prediction] | None = None) -> list[dict]:
    """summary() by level (key="level") or by phenomenon (key="phenomena").

    A sentence with several phenomena counts in each of them.
    """
    groups: dict = defaultdict(list)
    for item in items:
        values = item.phenomena if key == "phenomena" else (getattr(item, key),)
        for value in values:
            groups[value].append(item)
    rows = []
    for value in sorted(groups, key=str):
        group = groups[value]
        ids = {i.id for i in group}
        rows.append({"grupo": value, **summary(group, [p for p in predictions if p.id in ids], parser)})
    return rows


def per_sentence(items: list[TestItem], predictions: list[Prediction]) -> list[dict]:
    """One row per sentence: what was expected and what the LLM answered."""
    by_id = {p.id: p for p in predictions}
    rows = []
    for item in items:
        p = by_id.get(item.id)
        if p is None:
            continue
        answer = "sin JSON" if p.accepts is None else ("acepta" if p.accepts else f"rechaza ({p.error_type})")
        rows.append({
            "id": item.id,
            "nivel": item.level,
            "oracion": item.sentence,
            "fenomeno": ";".join(item.phenomena),
            "esperado": "acepta" if item.in_grammar else f"rechaza ({item.error_type})",
            "llm": answer,
            "acierta": p.accepts == item.in_grammar,
            "desvio": bool(p.accepts) and not item.in_grammar and item.valid_spanish,
            "arbol_en_gramatica": tree_follows_grammar(p.tree) if p.tree else None,
        })
    return rows


def _last_per_id(log: list[dict], system: str) -> list[dict]:
    """The answer that counts for each id (the last one, as ask_llm reuses)."""
    last = {}
    for entry in log:
        if entry.get("sistema") == system:
            last[entry["id"]] = entry
    return list(last.values())


def answer_format(log: list[dict], system: str) -> dict:
    """How well the LLM followed the "only the JSON" instruction."""
    entries = _last_per_id(log, system)
    raw = [e.get("respuesta_cruda", "") for e in entries]
    valid = [r for r in raw if prompts.parse_answer(r) is not None]
    return {
        "respuestas": len(raw),
        "json_valido": len(valid),
        "json_puro": sum(not prompts.is_fenced(r) for r in valid),
        "json_con_bloque_de_codigo": sum(prompts.is_fenced(r) for r in valid),
        "sin_json": len(raw) - len(valid),
    }


def cost_from_log(log: list[dict]) -> list[dict]:
    """Time and tokens per call, by system and model (answers that count only)."""
    rows = []
    for system in sorted({e.get("sistema") for e in log}):
        entries = _last_per_id(log, system)
        for model in sorted({e.get("modelo", "") for e in entries}):
            group = [e for e in entries if e.get("modelo", "") == model]
            times = [e["tiempo_ms"] for e in group if "tiempo_ms" in e]
            tokens_in = [e["tokens_entrada"] for e in group if "tokens_entrada" in e]
            tokens_out = [e["tokens_salida"] for e in group if "tokens_salida" in e]
            rows.append({
                "sistema": system,
                "modelo": model,
                "llamadas": len(group),
                "tiempo_ms_promedio": mean(times) if times else None,
                "tokens_entrada_promedio": mean(tokens_in) if tokens_in else None,
                "tokens_salida_promedio": mean(tokens_out) if tokens_out else None,
                "tokens_totales": sum(tokens_in) + sum(tokens_out) if tokens_in else None,
            })
    return rows
