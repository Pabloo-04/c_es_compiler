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
        # TODO(P3): skip NPbase → Prn. Otherwise compare with the Noun of Nom:
        #   - the Det (gender and number) or the Pos (number only),
        #   - the Adj inside Nom's AdjP, if any (gender and number).
        #   Use leaf.reading.features.gender / .number; None agrees with anything.
        raise NotImplementedError("TODO(P3): check_noun_phrase")

    def check_subject_verb(self, sentence: Node) -> None:
        # TODO(P3): head = subject_head(sentence), verb = main_verb(sentence).
        #   Number from the head; person: Prn has it, Noun is 3rd person.
        raise NotImplementedError("TODO(P3): check_subject_verb")


def check(tree: Node) -> list[AgreementError]:
    """Entry point used by the pipeline and the tests."""
    return AgreementChecker().check(tree)
