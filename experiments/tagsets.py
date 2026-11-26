"""Conversion of spaCy and Transformers outputs to our categories.

Executable copy of docs/gramatica_es.md, section 2.5 ("the conversion table
the notebooks must use, so nobody invents their own"). Owner: Person 1.

Both tools give Universal Dependencies UPOS tags; our categories are the ones
of section 2.2.
"""

CONVERSION = {"PRON": "Prn", "NOUN": "Noun", "PROPN": "Noun", "ADJ": "Adj",
              "VERB": "Verb", "AUX": "Verb", "ADP": "Prep"}

# Fallback when a model gives no features or dependencies (section 2.5).
POSSESSIVES = {"su", "sus", "mi", "mis", "tu", "tus"}
INTENSIFIERS = {"muy", "bastante", "poco", "tan"}


# ----------------------------------------------------------------------
# spaCy (has morphology and dependencies)
# ----------------------------------------------------------------------
def spacy_category(token) -> str:
    """Our category for a spaCy token (section 2.5)."""
    if token.pos_ == "DET":
        return "Pos" if "Yes" in token.morph.get("Poss") else "Det"
    if token.pos_ == "ADV":
        before_the_adj = token.head.pos_ == "ADJ" and token.i == token.head.i - 1
        return "Intens" if before_the_adj else "Adv"
    return CONVERSION.get(token.pos_, "X")


def spacy_pp_attachment(doc) -> str | None:
    """What the FIRST prepositional phrase attaches to (section 2.5): "verbo",
    "sustantivo", or None (no PP, or attached to something else)."""
    prep = next((t for t in doc if t.pos_ == "ADP" and t.dep_ == "case"), None)
    if prep is None:
        return None
    attached_to = prep.head.head          # head of the PP -> what it attaches to
    if attached_to.pos_ in ("VERB", "AUX"):
        return "verbo"
    if attached_to.pos_ in ("NOUN", "PROPN", "PRON"):
        return "sustantivo"
    return None


def spacy_output(id_: int, doc, time_ms: float) -> dict:
    """One line of results/spacy.jsonl (section 2.5)."""
    tokens = [t for t in doc if t.pos_ != "PUNCT"]
    root = next((t for t in doc if t.dep_ == "ROOT"), None)

    def role(dep: str) -> str:
        return next((t.text.lower() for t in doc if t.dep_ == dep and t.head == root), "")

    return {
        "id": id_, "sistema": "spacy", "acepta": None, "tipo_error": None,
        "etiquetas": [[t.text.lower(), spacy_category(t)] for t in tokens],
        "sujeto": role("nsubj"), "verbo": root.text.lower() if root else "",
        "objeto": role("obj"), "pp_adjunta": spacy_pp_attachment(doc), "arbol": None, "num_arboles": None,
        "tiempo_ms": time_ms, "error_ejecucion": None,
    }


# ----------------------------------------------------------------------
# Transformers (usually POS tags only: no features, no dependencies)
# ----------------------------------------------------------------------
def upos_category(upos: str, word: str) -> str | None:
    """Our category from a bare UPOS tag and the word. None = drop it (punctuation)."""
    if upos == "PUNCT":
        return None
    if upos == "DET":
        return "Pos" if word.lower() in POSSESSIVES else "Det"
    if upos == "ADV":
        return "Intens" if word.lower() in INTENSIFIERS else "Adv"
    return CONVERSION.get(upos, "X")
