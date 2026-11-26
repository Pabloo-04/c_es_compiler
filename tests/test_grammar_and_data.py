"""Grammar, lexicon and test set agree with docs/gramatica_es.md and with each
other. These pass from day 1 and protect the shared data while P1, P3 and P4
keep adding to it."""

from evaluation.formats import load_test_set
from spanish.grammar import (
    AUXILIARY, FIRST, PARSER_PRODUCTIONS, REPORT_PRODUCTIONS, START, as_bnf, check_grammar,
)
from spanish.lexicon import Lexicon
from spanish.tokens import Category


def test_parser_grammar_is_well_formed_and_has_no_left_recursion():
    assert check_grammar(PARSER_PRODUCTIONS) == []


def test_report_grammar_is_well_formed():
    assert check_grammar(REPORT_PRODUCTIONS, allow_left_recursion=True) == []


def test_bnf_text_matches_the_document():
    lines = as_bnf().splitlines()
    assert lines[0].split() == ["S", "→", "NP", "VP"]
    assert "NP'     → PP NP' | ε" in lines
    assert "VP'     → PP VP' | Adv VP' | ε" in lines


def test_auxiliary_nonterminals_are_the_epsilon_ones():
    with_epsilon = {p.left for p in PARSER_PRODUCTIONS if not p.right}
    assert with_epsilon == AUXILIARY


def test_first_sets():
    """Recompute FIRST from the productions and compare with grammar.FIRST."""
    def first(symbol, seen=()):
        if symbol not in {p.left for p in PARSER_PRODUCTIONS}:
            return {symbol}
        result = set()
        for p in PARSER_PRODUCTIONS:
            if p.left == symbol and p.right and p.right[0] not in seen:
                result |= first(p.right[0], seen + (symbol,))
        return result

    for symbol, expected in FIRST.items():
        assert first(symbol) == expected, symbol


def test_lexicon_loads_and_is_case_insensitive():
    lexicon = Lexicon.load()
    assert lexicon.lookup("Ella") == lexicon.lookup("ella") != ()
    assert lexicon.lookup("que") == ()


def test_lexicon_has_the_minimum_vocabulary_of_the_document():
    """docs/gramatica_es.md, section 1.3."""
    minimum = {
        Category.PRN: "él ella ellos",
        Category.DET: "un una el la los las",
        Category.POS: "sus su mi",
        Category.NOUN: "elefante pijamas niña perro perros manzana",
        Category.ADJ: "grande grandes gris grises pequeña rojos",
        Category.INTENS: "muy bastante",
        Category.ADV: "ayer hoy rápidamente",
        Category.PREP: "en con de",
        Category.VERB: "mata come duerme matan mató comió durmió mataron",
    }
    lexicon = Lexicon.load()
    for category, words in minimum.items():
        for word in words.split():
            assert category in {r.category for r in lexicon.lookup(word)}, f"{word} no es {category.value}"


def test_two_verb_tenses():
    tenses = {r.features.tense for w in Lexicon.load().words_by_category(Category.VERB) for r in Lexicon.load().lookup(w)}
    assert tenses == {"pres", "pret"}


def test_test_set_is_valid_and_covers_the_three_levels():
    items = load_test_set()  # validates every row
    assert {i.level for i in items} == {1, 2, 3}


def test_expected_tags_of_sentences_in_the_grammar_match_the_lexicon():
    """If this fails, the lexicon (P3) or the test set (P4) is out of date."""
    lexicon = Lexicon.load()
    for item in load_test_set():
        if not item.in_grammar:
            continue
        for word, category in item.tags:
            labels = {r.category.value for r in lexicon.lookup(word)}
            assert category in labels, f"id {item.id}: '{word}' no es {category} en el léxico"
