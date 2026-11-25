"""Shared contract: words and their grammatical readings.

Used by the lexer (P3), the parser (P2), the agreement checker (P3) and the
evaluation (P4). Agree on it on DAY 1; if it has to change, tell the whole team.

Code is in English; the linguistic labels that appear in the output are the
Spanish ones of the grammar (SUST, masc, sg...), as in docs/gramatica_es.md.

A word can be ambiguous ("bajo" is ADJ, PREP and V), so a Token carries ALL
its possible readings and the parser picks one.
"""

from dataclasses import dataclass, field
from enum import Enum


class Category(Enum):
    """Lexical (preterminal) categories. The value is the label used in trees."""

    DET = "DET"         # determinante: el, la, un, unos
    NOUN = "SUST"       # sustantivo: gato, casa
    PROPN = "NPROP"     # nombre propio: Ana, Madrid
    PRON = "PRON"       # pronombre personal sujeto: yo, ella, nosotros
    ADJ = "ADJ"         # adjetivo: negro, pequeña
    VERB = "V"          # verbo: come, comieron
    ADV = "ADV"         # adverbio: rápidamente, muy
    PREP = "PREP"       # preposición: en, con, de
    CONJ = "CONJ"       # conjunción: y, o  (TODO(P1): ¿entra en la gramática?)


# Allowed feature values (the strings that appear in data/lexicon.json).
GENDERS = {"masc", "fem"}
NUMBERS = {"sg", "pl"}
PERSONS = {1, 2, 3}
TENSES = {"presente", "preterito"}  # TODO(P1): confirm the two tenses of the grammar.


@dataclass(frozen=True)
class Features:
    """Morphological features. None = the feature does not apply.

    - gender:  "masc" | "fem"           (DET, SUST, ADJ, PRON)
    - number:  "sg" | "pl"              (DET, SUST, ADJ, PRON, V)
    - person:  1 | 2 | 3                (PRON, V; nouns are 3rd person)
    - tense:   "presente" | "preterito" (V)
    """

    gender: str | None = None
    number: str | None = None
    person: int | None = None
    tense: str | None = None

    def __post_init__(self) -> None:
        if self.gender is not None and self.gender not in GENDERS:
            raise ValueError(f"invalid gender {self.gender!r}")
        if self.number is not None and self.number not in NUMBERS:
            raise ValueError(f"invalid number {self.number!r}")
        if self.person is not None and self.person not in PERSONS:
            raise ValueError(f"invalid person {self.person!r}")
        if self.tense is not None and self.tense not in TENSES:
            raise ValueError(f"invalid tense {self.tense!r}")

    def __str__(self) -> str:
        """Compact form for the demo: "masc, sg" or "3, pl, preterito"."""
        values = [self.gender, self.number, self.person, self.tense]
        return ", ".join(str(v) for v in values if v is not None)


@dataclass(frozen=True)
class Reading:
    """One possible analysis of a word: gato -> (SUST, gato, masc, sg)."""

    category: Category
    lemma: str
    features: Features = field(default_factory=Features)

    def __str__(self) -> str:
        feats = str(self.features)
        return f"{self.category.value}({self.lemma}{', ' + feats if feats else ''})"


@dataclass(frozen=True)
class Token:
    """A word of the sentence.

    - word:     the word as written, without the final punctuation ("Gatos").
    - position: index of the word in the sentence, starting at 1.
    - column:   column of its first character, starting at 1.
    - readings: every reading found in the lexicon (at least one, unless the
                word is unknown; unknown words produce a LexicalError).
    """

    word: str
    position: int
    column: int
    readings: tuple[Reading, ...] = ()

    @property
    def is_ambiguous(self) -> bool:
        return len(self.readings) > 1

    def readings_of(self, category: Category) -> list[Reading]:
        """Readings of this word with the given category (helper for the parser)."""
        return [r for r in self.readings if r.category is category]

    def __str__(self) -> str:
        options = " | ".join(str(r) for r in self.readings) or "?"
        return f"{self.position}:{self.column}\t{self.word:<14} {options}"
