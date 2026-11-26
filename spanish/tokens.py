"""Shared contract: words and their grammatical readings.

Used by the lexer (P3), the parser (P2), the agreement checker (P3) and the
evaluation (P4). Categories and feature values are the ones agreed in
docs/gramatica_es.md (sections 1.3 and 2.2); do not change them without
telling the whole team.

A word can be ambiguous, so a Token carries ALL its possible readings and the
parser picks one. A word that is not in the lexicon gets one reading of
category X ("any other word, outside the grammar"), so the parser rejects the
sentence as a syntax error, as the agreed format expects.
"""

from dataclasses import dataclass, field
from enum import Enum


class Category(Enum):
    """Closed set of categories (docs/gramatica_es.md, 2.2). Value = label in trees and outputs."""

    PRN = "Prn"         # pronombre: él, ella, ellos
    DET = "Det"         # determinante: el, la, un, los
    POS = "Pos"         # posesivo: su, sus, mi
    NOUN = "Noun"       # sustantivo: elefante, niña
    ADJ = "Adj"         # adjetivo: grande, rojos
    INTENS = "Intens"   # intensificador: muy, bastante
    ADV = "Adv"         # adverbio: ayer, rápidamente
    VERB = "Verb"       # verbo: come, mató
    PREP = "Prep"       # preposición: en, con, de
    X = "X"             # cualquier otra palabra (fuera de la gramática)


CATEGORY_BY_LABEL = {c.value: c for c in Category}

# Allowed feature values (docs/gramatica_es.md, 1.3).
GENDERS = {"m", "f"}
NUMBERS = {"sg", "pl"}
PERSONS = {1, 2, 3}
TENSES = {"pres", "pret"}


@dataclass(frozen=True)
class Features:
    """Morphological features. None = the feature does not apply or is not marked.

    - gender:  "m" | "f"        (Det, Noun, Adj, Prn; Pos and invariable
                                  adjectives such as "grande" have none)
    - number:  "sg" | "pl"      (Det, Pos, Noun, Adj, Prn, Verb)
    - person:  1 | 2 | 3        (Prn, Verb; nouns are 3rd person)
    - tense:   "pres" | "pret"  (Verb)
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
        """Compact form for the demo: "m, sg" or "sg, 3, pret"."""
        values = [self.gender, self.number, self.person, self.tense]
        return ", ".join(str(v) for v in values if v is not None)


@dataclass(frozen=True)
class Reading:
    """One possible analysis of a word: niña -> Noun (f, sg)."""

    category: Category
    lemma: str
    features: Features = field(default_factory=Features)

    def __str__(self) -> str:
        feats = str(self.features)
        return f"{self.category.value}({self.lemma}{', ' + feats if feats else ''})"


@dataclass(frozen=True)
class Token:
    """A word of the sentence.

    - word:     the word as written, without the final period ("Ella").
    - position: index of the word in the sentence, starting at 1.
    - column:   column of its first character, starting at 1.
    - readings: every reading found in the lexicon; (Reading(X),) if unknown.
    """

    word: str
    position: int
    column: int
    readings: tuple[Reading, ...] = ()

    @property
    def is_ambiguous(self) -> bool:
        return len(self.readings) > 1

    @property
    def is_unknown(self) -> bool:
        return all(r.category is Category.X for r in self.readings)

    def readings_of(self, category: Category) -> list[Reading]:
        """Readings of this word with the given category (helper for the parser)."""
        return [r for r in self.readings if r.category is category]

    def has(self, *categories: Category) -> bool:
        """Can this word be any of these categories? (FIRST-set checks in the parser)."""
        return any(r.category in categories for r in self.readings)

    def __str__(self) -> str:
        options = " | ".join(str(r) for r in self.readings) or "?"
        return f"{self.position}:{self.column}\t{self.word:<14} {options}"
