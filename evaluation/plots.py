"""Plots for the report (results/figures/).  Owner: Person 4.

    python -m evaluation.metrics     # computes the metrics and calls save_all()

Needs matplotlib (requirements-experiments.txt). Every plot is also a table
in results/metricas.md, so the numbers can be read without the colors.

Each system always has the same color in every plot (the color follows the
system, not its position), and color is never the only cue: plots with more
than one system have a legend, and the bars carry their value.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no window: only files
import matplotlib.pyplot as plt  # noqa: E402

from .formats import CATEGORIES, RESULTS_DIR, SYSTEMS, TestItem  # noqa: E402
from .metrics import SYSTEM_NAMES, NO_STRUCTURE, Pair, value  # noqa: E402

FIGURES_DIR = RESULTS_DIR / "figures"

# Fixed categorical order, validated for color-vision deficiencies.
SYSTEM_COLORS = {
    "parser": "#2a78d6",
    "spacy": "#eb6834",
    "transformers": "#1baf7a",
    "llm_zero": "#eda100",
    "llm_few": "#e87ba4",
}
SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e1e0d9"
REFERENCE_COLORS = {"aceptacion": "#52514e", "aceptacion_espanol": "#b5b3aa"}  # neutral: not systems
LEVELS = ("1", "2", "3")
LEVEL_NAMES = {"1": "Nivel 1\n(simples)", "2": "Nivel 2\n(intermedias)", "3": "Nivel 3\n(complejas)"}


def _style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(TEXT_SECONDARY)
    ax.tick_params(colors=TEXT_SECONDARY, length=0)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _figure(width: float, height: float, ncols: int = 1):
    plt.rcParams.update({"font.size": 10, "text.color": TEXT})
    fig, axes = plt.subplots(1, ncols, figsize=(width, height), facecolor=SURFACE, squeeze=False)
    return fig, list(axes[0])


def _label(v: float) -> str:
    return "1" if v >= 0.995 else f"{v:.2f}".lstrip("0")


def _grouped_bars(ax, groups: list[str], series: dict[str, list[float | None]],
                  colors: dict[str, str], names: dict[str, str]) -> None:
    """Bars grouped by `groups`, one per series. None is drawn as a "—" (no data)."""
    n = max(len(series), 1)
    width = 0.8 / n
    for i, (key, values) in enumerate(series.items()):
        xs = [g + (i - (n - 1) / 2) * width for g in range(len(groups))]
        bars = ax.bar(xs, [v or 0 for v in values], width * 0.9, color=colors[key],
                      label=names.get(key, key), edgecolor=SURFACE, linewidth=1)
        for bar, v in zip(bars, values):
            ax.annotate("—" if v is None else _label(v),
                        (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        xytext=(0, 2), textcoords="offset points", ha="center", va="bottom",
                        fontsize=7, color=TEXT_SECONDARY)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups, color=TEXT)
    ax.set_ylim(0, 1.12)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1])


def _legend(fig, ax, ncol: int) -> None:
    handles, labels = ax.get_legend_handles_labels()
    if len(handles) > 1:
        fig.legend(handles, labels, loc="lower center", ncol=ncol, frameon=False,
                   bbox_to_anchor=(0.5, -0.1), labelcolor=TEXT)


def _title(fig, text: str) -> None:
    fig.suptitle(text, x=0.01, ha="left", y=1.02, color=TEXT)


def _save(fig, name: str) -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / name
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


def _systems_with(rows, comparison) -> list[str]:
    present = {r["sistema"] for r in rows if r["comparacion"] == comparison}
    return [s for s in SYSTEMS if s in present]


# ----------------------------------------------------------------------
def plot_acceptance(rows) -> Path | None:
    systems = _systems_with(rows, "aceptacion")
    if not systems:
        return None
    metrics = {"precision": "Precisión", "cobertura": "Cobertura", "rechazo_correcto": "Rechazo\ncorrecto",
               "exactitud": "Exactitud", "tipo_error": "Tipo de\nerror"}
    series = {s: [value(rows, s, "aceptacion", m) for m in metrics] for s in systems}
    fig, (ax,) = _figure(7.5, 3.6)
    _style(ax)
    _grouped_bars(ax, list(metrics.values()), series, SYSTEM_COLORS, SYSTEM_NAMES)
    _legend(fig, ax, len(systems))
    _title(fig, "Aceptación contra en_gramatica (las reglas de la gramática)")
    return _save(fig, "aceptacion.png")


def plot_rules_vs_spanish(rows) -> Path | None:
    """Accuracy against the rules and against Spanish: who follows which?"""
    systems = _systems_with(rows, "aceptacion")
    if not systems:
        return None
    series = {c: [value(rows, s, c, "exactitud") for s in systems] for c in REFERENCE_COLORS}
    fig, (ax,) = _figure(max(4.5, 1.6 * len(systems) + 2), 3.6)
    _style(ax)
    _grouped_bars(ax, [SYSTEM_NAMES[s] for s in systems], series, REFERENCE_COLORS,
                  {"aceptacion": "contra en_gramatica (las reglas)",
                   "aceptacion_espanol": "contra espanol_valido (el español)"})
    _legend(fig, ax, 2)
    _title(fig, "Exactitud de la aceptación según la referencia")
    return _save(fig, "reglas_vs_espanol.png")


def plot_by_level(rows) -> Path:
    panels = [("aceptacion", "exactitud", "Exactitud de la aceptación"),
              ("etiquetado", "exactitud", "Exactitud del etiquetado")]
    panels = [p for p in panels if _systems_with(rows, p[0])]
    fig, axes = _figure(5 * len(panels), 3.6, ncols=len(panels))
    for ax, (comparison, metric, title) in zip(axes, panels):
        _style(ax)
        series = {s: [value(rows, s, comparison, metric, lv) for lv in LEVELS]
                  for s in _systems_with(rows, comparison)}
        _grouped_bars(ax, [LEVEL_NAMES[lv] for lv in LEVELS], series, SYSTEM_COLORS, SYSTEM_NAMES)
        ax.set_title(title, loc="left", color=TEXT, fontsize=10)
    _legend(fig, axes[-1], len(SYSTEMS))
    _title(fig, "Por nivel de complejidad")
    return _save(fig, "por_nivel.png")


def plot_functions(rows) -> Path | None:
    systems = _systems_with(rows, "funciones")
    if not systems:
        return None
    groups = {("funciones", "sujeto"): "Sujeto", ("funciones", "verbo"): "Verbo",
              ("funciones", "objeto"): "Objeto", ("estructura", "pp_adjunta"): "Unión\nde la PP",
              ("estructura", "ambiguas_detectadas"): "PP ambiguas\ndetectadas"}
    series = {s: [None if c == "estructura" and s in NO_STRUCTURE else value(rows, s, c, m)
                  for c, m in groups] for s in systems}
    fig, (ax,) = _figure(7.5, 3.6)
    _style(ax)
    _grouped_bars(ax, list(groups.values()), series, SYSTEM_COLORS, SYSTEM_NAMES)
    _legend(fig, ax, len(systems))
    _title(fig, "Funciones sintácticas y unión de la frase preposicional")
    return _save(fig, "funciones_pp.png")


def plot_categories(rows) -> Path | None:
    """Heatmap system × category of the tagging recall (one hue, light to dark)."""
    systems = _systems_with(rows, "etiquetado_categoria")
    if not systems:
        return None
    categories = [c for c in CATEGORIES
                  if any(value(rows, s, "etiquetado_categoria", f"cobertura_{c}") is not None for s in systems)]
    matrix = [[value(rows, s, "etiquetado_categoria", f"cobertura_{c}") for c in categories] for s in systems]
    fig, (ax,) = _figure(0.75 * len(categories) + 2, 0.55 * len(systems) + 1.4)
    shown = [[v if v is not None else float("nan") for v in row] for row in matrix]
    ax.imshow(shown, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    for i, row in enumerate(matrix):
        for j, v in enumerate(row):
            ax.text(j, i, "—" if v is None else _label(v), ha="center", va="center", fontsize=8,
                    color="white" if v is not None and v > 0.75 else TEXT)
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, color=TEXT)
    ax.set_yticks(range(len(systems)))
    ax.set_yticklabels([SYSTEM_NAMES[s] for s in systems], color=TEXT)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    _title(fig, "Cobertura del etiquetado por categoría")
    return _save(fig, "etiquetado_categoria.png")


def save_all(items: list[TestItem], rows: list[dict], all_pairs: dict[str, list[Pair]]) -> list[Path]:
    if not rows:
        return []
    paths = [plot_acceptance(rows), plot_rules_vs_spanish(rows), plot_by_level(rows),
             plot_functions(rows), plot_categories(rows)]
    return [p for p in paths if p is not None]
