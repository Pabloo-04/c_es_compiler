"""Agreement checker.  Owner: Person 3 (the Phase 2 version of semantico.py).

Input:  the tree built by the parser (leaves carry their Reading).
Output: list of AgreementError (empty = the sentence agrees).

Rules (docs/gramatica_es.md, 1.3), checked on EVERY NPbase of the tree
(subject, object and the NPs inside PPs):

  1. Inside the NP: Det/Pos, Noun and Adj agree in gender and number.
       "los perros rojos" ✔   "la elefante" ✘   "los perro" ✘
     Possessives have no gender (su, sus): only number is checked.
     A missing feature agrees with anything: "grande" has no gender.
  2. Subject-verb: the head of the subject NP and the verb agree in number
     and person.
       "los perros comen" ✔   "los perros come" ✘
     Nouns are 3rd person; pronouns carry their own person.

Where the pieces are in the (flattened) tree:
  S → NP VP;  NP → NPbase PP*;  NPbase → Prn | Det Nom | Pos Nom;
  Nom → Noun AdjP?;  AdjP → Adj | Intens Adj;  VP → Verb NP? (PP | Adv)*

Message format (Spanish), reported at the word that breaks agreement:
  "el determinante 'la' no concuerda en género con 'elefante'"
  "el adjetivo 'grises' no concuerda en número con 'elefante'"
  "el verbo 'come' (singular) no concuerda con el sujeto 'perros' (plural)"
"""

from .errors import AgreementError
from .tree import Node

NUMBER_NAMES = {"sg": "singular", "pl": "plural"}
CATEGORY_NAMES = {"Det": "determinante", "Pos": "posesivo", "Adj": "adjetivo"}


def differ(a, b) -> bool:
    """True when two feature values clash. A missing value (None) agrees with anything."""
    return a is not None and b is not None and a != b


def person_name(person: int) -> str:
    return f"{person}.ª persona"


def subject_head(sentence: Node) -> Node | None:
    """Leaf of the subject's head: the Prn or the Noun of S → NP → NPbase."""
    np = sentence.child("NP")
    base = np.child("NPbase") if np else None
    if base is None:
        return None
    if base.child("Prn"):
        return base.child("Prn")
    nom = base.child("Nom")
    return nom.child("Noun") if nom else None


def main_verb(sentence: Node) -> Node | None:
    vp = sentence.child("VP")
    return vp.child("Verb") if vp else None


class AgreementChecker:
    def __init__(self) -> None:
        self.errors: list[AgreementError] = []

    def error(self, message: str, leaf: Node) -> None:
        position = leaf.token.position if leaf.token else None
        self.errors.append(AgreementError(position, leaf.word, message))

    def check(self, tree: Node) -> list[AgreementError]:
        for base in tree.find_all("NPbase"):
            self.check_noun_phrase(base)
        self.check_subject_verb(tree)
        return self.errors

    def check_noun_phrase(self, base: Node) -> None:
        """Det/Pos, Noun and Adj of one NPbase agree (gender and number)."""
        if base.child("Prn"):                 # a pronoun has nothing to agree with
            return
        nom = base.child("Nom")
        noun = nom.child("Noun") if nom else None
        if noun is None or noun.reading is None:
            return
        adjp = nom.child("AdjP")
        modifiers = [base.child("Det") or base.child("Pos"), adjp.child("Adj") if adjp else None]
        for leaf in modifiers:
            if leaf is not None and leaf.reading is not None:
                self.check_against_noun(leaf, noun)

    def check_against_noun(self, leaf: Node, noun: Node) -> None:
        """Compare a Det/Pos/Adj with its noun; one error per word, naming what fails."""
        mine, theirs = leaf.reading.features, noun.reading.features
        failing = []
        if differ(mine.gender, theirs.gender):
            failing.append("género")
        if differ(mine.number, theirs.number):
            failing.append("número")
        if failing:
            self.error(
                f"el {CATEGORY_NAMES[leaf.label]} '{leaf.word}' no concuerda en "
                f"{' y '.join(failing)} con '{noun.word}'",
                leaf,
            )

    def check_subject_verb(self, sentence: Node) -> None:
        """The head of the subject and the verb agree in number and person."""
        head, verb = subject_head(sentence), main_verb(sentence)
        if head is None or verb is None or head.reading is None or verb.reading is None:
            return
        subject, action = head.reading.features, verb.reading.features
        # Nouns are always 3rd person; a pronoun carries its own.
        subject_person = 3 if head.label == "Noun" else subject.person

        number_fails = differ(subject.number, action.number)
        person_fails = differ(subject_person, action.person)
        if not (number_fails or person_fails):
            return

        def describe(number, person) -> str:
            parts = []
            if number_fails:
                parts.append(NUMBER_NAMES[number])
            if person_fails:
                parts.append(person_name(person))
            return ", ".join(parts)

        self.error(
            f"el verbo '{verb.word}' ({describe(action.number, action.person)}) no concuerda "
            f"con el sujeto '{head.word}' ({describe(subject.number, subject_person)})",
            verb,
        )


def check(tree: Node) -> list[AgreementError]:
    """Entry point used by the pipeline and the tests."""
    return AgreementChecker().check(tree)
