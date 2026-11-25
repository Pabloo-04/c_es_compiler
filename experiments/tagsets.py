"""Map other tagsets to our categories, to compare spaCy/Transformers with the parser.

Owner: Person 1. spaCy and most HuggingFace Spanish taggers use Universal
Dependencies POS tags (UPOS). Our categories are the ones of spanish/tokens.py.

PROPOSAL: check the cases marked TODO with real outputs.
"""

UPOS_TO_OURS: dict[str, str] = {
    "DET": "DET",
    "NOUN": "SUST",
    "PROPN": "NPROP",
    "PRON": "PRON",
    "ADJ": "ADJ",
    "VERB": "V",
    "AUX": "V",       # TODO(P1): "ha comido" / "es": ¿entra en la gramática?
    "ADV": "ADV",
    "ADP": "PREP",
    "CCONJ": "CONJ",
    "SCONJ": "CONJ",
    "PUNCT": None,    # punctuation is dropped
    "NUM": "DET",     # TODO(P1): "dos gatos": the grammar has no numerals
}

# Morphological features (spaCy token.morph / UD feats) -> our values.
UD_GENDER = {"Masc": "masc", "Fem": "fem"}
UD_NUMBER = {"Sing": "sg", "Plur": "pl"}
UD_TENSE = {"Pres": "presente", "Past": "preterito"}   # TODO(P1): Imp (imperfecto) -> ?


def upos_to_ours(tag: str) -> str | None:
    """None means: drop the word (punctuation). Unknown tags come back as 'OTRO'."""
    return UPOS_TO_OURS.get(tag, "OTRO")
