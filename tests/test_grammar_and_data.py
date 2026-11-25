"""Grammar, lexicon and data files are consistent. These pass from day 1 and
protect the shared data while P1, P3 and P4 keep adding to it."""

from evaluation.formats import load_test_set
from spanish.grammar import PRODUCTIONS, START, as_bnf, check_grammar
from spanish.lexicon import Lexicon
from spanish.tokens import Category
from spanish.tree import Node


def test_grammar_is_well_formed():
    assert check_grammar() == []


def test_bnf_text_for_docs_and_prompt():
    text = as_bnf()
    assert text.splitlines()[0].startswith(f"{START} ")
    assert "SN" in text and "::=" in text


def test_lexicon_loads_and_is_case_insensitive():
    lexicon = Lexicon.load()
    assert len(lexicon) > 0
    assert lexicon.lookup("Gato") == lexicon.lookup("gato") != ()
    assert lexicon.lookup("xyz") == ()


def test_lexicon_ambiguous_word():
    categories = {r.category for r in Lexicon.load().lookup("bajo")}
    assert categories == {Category.ADJ, Category.PREP}


def test_test_set_is_valid():
    items = load_test_set()  # validates every item
    assert {i.level for i in items} == {"simple", "intermedia", "compleja"}


def test_expected_trees_use_the_grammar():
    """Every expected tree must be derivable with grammar.PRODUCTIONS.

    If this fails after P1 changes the grammar, either the test set (P4) or
    the grammar is out of date: fix it together.
    """
    rules = {(p.left, p.right) for p in PRODUCTIONS}
    for item in load_test_set():
        if not item.tree:
            continue
        for node in Node.from_bracketed(item.tree).walk():
            if node.is_leaf:
                continue
            rhs = tuple(child.label for child in node.children)
            assert (node.label, rhs) in rules, f"{item.id}: {node.label} → {' '.join(rhs)} no está en la gramática"


def test_expected_tree_words_are_in_the_lexicon_with_that_category():
    lexicon = Lexicon.load()
    for item in load_test_set():
        if not item.tree:
            continue
        for leaf in Node.from_bracketed(item.tree).leaves():
            labels = {r.category.value for r in lexicon.lookup(leaf.word)}
            assert leaf.label in labels, f"{item.id}: '{leaf.word}' no es {leaf.label} en el léxico"
