"""Agreement checker.  Owner: Person 3 (the Phase 2 version of semantic.py).

Input:  the tree built by the parser (leaves carry their Reading).
Output: list of AgreementError (empty = the sentence agrees).

What a CFG cannot express without multiplying its rules (see the Phase 1
reflection, fase1/README.md): features that must match between words.

Checks:
  1. Inside each SN: DET, SUST and every ADJ of its SA agree in gender and number.
       "el gato negro" ✓   "la gato negro" ✗ (género)   "el gatos" ✗ (número)
  2. Subject-verb: the SN that is the subject of O agrees with the V of SV
     in number and person.
       "los niños corren" ✓   "los niños corre" ✗ (número)
     Nouns and proper names are 3rd person; pronouns carry their own person.

Message format (Spanish), e.g.:
  "el determinante 'la' no concuerda en género con 'gato'"
  "el sujeto 'los niños' (plural) no concuerda con el verbo 'corre' (singular)"
"""

from .errors import AgreementError
from .tree import Node


class AgreementChecker:
    def __init__(self) -> None:
        self.errors: list[AgreementError] = []

    def error(self, message: str, leaf: Node) -> None:
        """Report at the word that breaks agreement (usually the later one)."""
        position = leaf.token.position if leaf.token else None
        self.errors.append(AgreementError(position, leaf.word, message))

    def check(self, tree: Node) -> list[AgreementError]:
        for noun_phrase in tree.find_all("SN"):
            self.check_noun_phrase(noun_phrase)
        self.check_subject_verb(tree)
        return self.errors

    def check_noun_phrase(self, sn: Node) -> None:
        # TODO(P3): take the DET, SUST and the ADJ inside its SA (sn.child("SA")),
        #           compare leaf.reading.features.gender / .number.
        #           Skip the SN → NPROP / PRON cases (nothing to compare).
        raise NotImplementedError("TODO(P3): check_noun_phrase")

    def check_subject_verb(self, sentence: Node) -> None:
        # TODO(P3): subject = sentence.child("SN"), verb = the V of sentence.child("SV").
        #           Number: from SUST / PRON (NPROP: sg).
        #           Person: PRON has it; SUST and NPROP are 3rd person.
        raise NotImplementedError("TODO(P3): check_subject_verb")


def check(tree: Node) -> list[AgreementError]:
    """Entry point used by the pipeline and the tests."""
    return AgreementChecker().check(tree)
