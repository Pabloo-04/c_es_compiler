"""Tree visualization tests.  Owner: Person 3.

graph_parts() and to_dot() need nothing installed. render() needs the Graphviz
program ("dot"); ascii_tree() needs nltk. Each test is skipped if its tool is missing.
"""

import shutil

import pytest

from helpers import tree_from_lexicon as build
from spanish.agreement import check
from spanish.trees import ascii_tree, graph_parts, render, to_dot

SENTENCE = "(S (NP (NPbase (Prn ella))) (VP (Verb come) (NP (NPbase (Det una) (Nom (Noun manzana))))))"
DISAGREES = "(S (NP (NPbase (Det la) (Nom (Noun elefante) (AdjP (Adj grises))))) (VP (Verb duerme)))"


def test_words_keep_sentence_order():
    _, _, words = graph_parts(build(SENTENCE))
    assert [w[1] for w in words] == ["ella", "come", "una", "manzana"]


def test_every_edge_connects_existing_nodes():
    nodes, edges, words = graph_parts(build(SENTENCE))
    ids = {n[0] for n in nodes} | {w[0] for w in words}
    assert all(parent in ids and child in ids for parent, child in edges)
    assert len(edges) == len(nodes) - 1          # a tree: one parent per node except the root


def test_words_with_agreement_errors_are_marked():
    tree = build(DISAGREES)
    _, _, words = graph_parts(tree, errors=check(tree))
    assert {text for _, text, _, is_error in words if is_error} == {"la", "grises"}
    assert "#c00000" in to_dot(tree, errors=check(tree))


def test_without_errors_nothing_is_marked():
    _, _, words = graph_parts(build(SENTENCE))
    assert not any(is_error for *_, is_error in words)


@pytest.mark.skipif(shutil.which("dot") is None, reason="Graphviz no está instalado")
def test_render_creates_an_image(tmp_path):
    path = render(build(SENTENCE), tmp_path / "ella.png")
    assert path.exists() and path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.skipif(shutil.which("dot") is None, reason="Graphviz no está instalado")
def test_render_takes_the_format_from_the_extension(tmp_path):
    assert render(build(SENTENCE), tmp_path / "ella.svg").suffix == ".svg"


def test_ascii_tree_contains_the_words():
    pytest.importorskip("nltk")
    drawing = ascii_tree(build(SENTENCE))
    assert all(word in drawing for word in ["ella", "come", "una", "manzana"])
