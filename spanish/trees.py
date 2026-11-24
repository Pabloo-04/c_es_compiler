"""Tree visualization.  Owner: Person 3.

Two backends (choose one or keep both):
  - graphviz: nice PNG/SVG images for the report and the presentation.
    Needs the Python package AND the system program (macOS: brew install graphviz).
  - nltk.Tree: ASCII drawing in the terminal (tree.pretty_print()) and a
    Tk window; no system program needed.

Imports are done inside the functions, so the rest of the project works
even if these optional libraries are not installed.
"""

from pathlib import Path

from .tree import Node


def to_nltk(tree: Node):
    """Node -> nltk.Tree. The bracketed format is the same one NLTK reads."""
    from nltk import Tree  # optional dependency

    return Tree.fromstring(tree.to_bracketed())


def ascii_tree(tree: Node) -> str:
    """ASCII drawing for the terminal demo (uses nltk)."""
    # TODO(P3): return the text of to_nltk(tree).pretty_print()
    #           (hint: nltk's TreePrettyPrinter(...).text()).
    raise NotImplementedError("TODO(P3): ascii_tree")


def to_graphviz(tree: Node, title: str | None = None):
    """Node -> graphviz.Digraph: one graph node per tree node, words as leaves."""
    # TODO(P3): import graphviz; walk the tree giving each node a unique id
    #           (e.g. a counter); phrases as ellipses, words as plain text;
    #           optional: color leaves by category, or by agreement error.
    raise NotImplementedError("TODO(P3): to_graphviz")


def render(tree: Node, path: Path | str, fmt: str = "png") -> Path:
    """Save the drawing to results/figures/... and return the file path."""
    # TODO(P3): to_graphviz(tree).render(...) with cleanup=True.
    raise NotImplementedError("TODO(P3): render")
