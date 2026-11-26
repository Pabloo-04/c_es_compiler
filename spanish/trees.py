"""Tree visualization.  Owner: Person 3.

Two backends (choose one or keep both):
  - graphviz: nice PNG/SVG images for the report and the presentation.
    Needs the Python package AND the system program (macOS: brew install graphviz).
  - nltk.Tree: ASCII drawing in the terminal (tree.pretty_print()) and a
    Tk window; no system program needed.

Imports are done inside the functions, so the rest of the project works
even if these optional libraries are not installed.
"""

import shutil
import subprocess
from pathlib import Path

from .tree import Node

# Fill color of each lexical category (leaves). Phrases (NP, VP...) stay white.
CATEGORY_COLORS = {
    "Prn": "#d6e4ff", "Det": "#e8e8e8", "Pos": "#e8e8e8", "Noun": "#ffe4b5",
    "Adj": "#d5f5d5", "Intens": "#eaf7c8", "Adv": "#f3d9fa", "Verb": "#ffd1d1",
    "Prep": "#d4f1f4", "X": "#ffffff",
}
ERROR_COLOR = "#ff6b6b"      # leaf of a word that breaks agreement
IMAGE_FORMATS = ("png", "svg", "pdf")


def to_nltk(tree: Node):
    """Node -> nltk.Tree. The bracketed format is the same one NLTK reads."""
    from nltk import Tree  # optional dependency

    return Tree.fromstring(tree.to_bracketed())


def ascii_tree(tree: Node) -> str:
    """ASCII drawing for the terminal demo (uses nltk)."""
    from nltk.tree import TreePrettyPrinter  # optional dependency

    return TreePrettyPrinter(to_nltk(tree)).text()


def graph_parts(tree: Node, errors=None):
    """Walk the tree once and describe the drawing (no graphviz needed).

    Returns (nodes, edges, words):
      nodes: [(id, label, fill_color)]   phrases and categories (ellipses)
      edges: [(parent_id, child_id)]
      words: [(id, text, parent_id, is_error)]  the words, drawn as plain text
             under their category; all on the same row at the bottom.
    `errors` is a list of Diagnostics (agreement errors): the words they point
    to are drawn in red.
    """
    bad_positions = {e.position for e in (errors or []) if e.position is not None}
    nodes, edges, words = [], [], []
    counter = 0

    def visit(node: Node, parent: str | None) -> None:
        nonlocal counter
        node_id = f"n{counter}"
        counter += 1
        is_error = node.token is not None and node.token.position in bad_positions
        if node.is_leaf:
            fill = ERROR_COLOR if is_error else CATEGORY_COLORS.get(node.label, "#ffffff")
            nodes.append((node_id, node.label, fill))
            word_id = f"w{counter}"
            counter += 1
            words.append((word_id, node.word, node_id, is_error))
        else:
            nodes.append((node_id, node.label, "#ffffff"))
            for child in node.children:
                visit(child, node_id)
        if parent is not None:
            edges.append((parent, node_id))

    visit(tree, None)
    return nodes, edges, words


def to_graphviz(tree: Node, title: str | None = None, errors=None):
    """Node -> graphviz.Digraph: phrases and categories as ellipses, words as text."""
    import graphviz  # optional dependency (also needs the Graphviz program)

    nodes, edges, words = graph_parts(tree, errors)
    graph = graphviz.Digraph("arbol", format="png")
    graph.attr("graph", dpi="150", nodesep="0.3", ranksep="0.45")
    if title:
        graph.attr(label=title, labelloc="t", fontname="Helvetica", fontsize="16")
    graph.attr("node", fontname="Helvetica", fontsize="13")
    graph.attr("edge", arrowhead="none")
    for node_id, label, fill in nodes:
        graph.node(node_id, label, shape="ellipse", style="filled", fillcolor=fill)
    for parent, child in edges:
        graph.edge(parent, child)
    with graph.subgraph() as row:               # every word on the same bottom row
        row.attr(rank="same")
        for word_id, text, parent, is_error in words:
            color = "#c00000" if is_error else "black"
            row.node(word_id, text, shape="plaintext", fontcolor=color,
                     fontname="Helvetica-Bold" if is_error else "Helvetica")
    for word_id, _, parent, _ in words:
        graph.edge(parent, word_id, style="dotted")
    return graph


def render(tree: Node, path: Path | str, fmt: str | None = None, errors=None, title: str | None = None) -> Path:
    """Save the drawing (png, svg or pdf) and return the file path.

    The format is taken from the file extension (default png).
    Uses the Python package `graphviz`; if it is missing, calls the `dot` program directly.
    """
    path = Path(path)
    fmt = fmt or (path.suffix.lstrip(".").lower() if path.suffix.lstrip(".").lower() in IMAGE_FORMATS else "png")
    target = path.with_suffix(f".{fmt}")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        graph = to_graphviz(tree, title, errors)
    except ImportError:
        _render_with_dot(tree, target, fmt, errors, title)
        return target
    graph.format = fmt
    graph.render(filename=target.stem, directory=str(target.parent), cleanup=True)
    return target


def to_dot(tree: Node, title: str | None = None, errors=None) -> str:
    """The same drawing as DOT text (used when the python package `graphviz` is missing)."""
    nodes, edges, words = graph_parts(tree, errors)
    lines = ["digraph arbol {", '  graph [dpi=150, nodesep=0.3, ranksep=0.45];',
             '  node [fontname="Helvetica", fontsize=13];', "  edge [arrowhead=none];"]
    if title:
        lines.append(f'  label="{title}"; labelloc=t; fontsize=16;')
    for node_id, label, fill in nodes:
        lines.append(f'  {node_id} [label="{label}", shape=ellipse, style=filled, fillcolor="{fill}"];')
    for parent, child in edges:
        lines.append(f"  {parent} -> {child};")
    lines.append("  { rank=same;")
    for word_id, text, _, is_error in words:
        color = "#c00000" if is_error else "black"
        lines.append(f'    {word_id} [label="{text}", shape=plaintext, fontcolor="{color}"];')
    lines.append("  }")
    for word_id, _, parent, _ in words:
        lines.append(f"  {parent} -> {word_id} [style=dotted];")
    lines.append("}")
    return "\n".join(lines)


def _render_with_dot(tree: Node, target: Path, fmt: str, errors, title) -> None:
    dot = shutil.which("dot")
    if dot is None:
        raise RuntimeError(
            "No se encontró Graphviz: instale el programa (comando 'dot') y agréguelo al PATH."
        )
    subprocess.run([dot, f"-T{fmt}", "-o", str(target)], input=to_dot(tree, title, errors),
                   text=True, encoding="utf-8", check=True)
