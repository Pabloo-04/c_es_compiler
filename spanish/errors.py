"""Diagnostics shared by every phase (adapted from fase1/compiler/errors.py).

Phases do NOT stop at the first error: they collect every diagnostic.

Single format (in Spanish, like all the output):
    "Palabra 2 ('elefante'): el determinante 'la' no concuerda en género con 'elefante'"
    "Oración: falta el verbo"                       (when no single word is to blame)

Hierarchy:
    Diagnostic
    ├── LexicalError     invalid character ("#", "3")          tipo_error "sintactico"
    ├── ParseError       structure or word outside the grammar  tipo_error "sintactico"
    └── AgreementError   gender/number/person mismatch          tipo_error "concordancia"

`error_type` is the value written in the "tipo_error" field of the results
(docs/gramatica_es.md, 2.4). The agreed format has only two error types, so a
lexical error also counts as "sintactico": the sentence cannot be derived.
Unknown words are not lexical errors: they are tagged X and the parser
rejects them.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Diagnostic:
    position: int | None    # word index (1-based); None = the whole sentence
    word: str | None        # the word as written, for the message
    message: str            # just the cause, in Spanish

    kind: ClassVar[str] = "diagnóstico"
    error_type: ClassVar[str] = "sintactico"

    def __str__(self) -> str:
        if self.position is None:
            return f"Oración: {self.message}"
        return f"Palabra {self.position} ('{self.word}'): {self.message}"

    def labeled(self) -> str:
        """"[error de concordancia] Palabra 2 ('elefante'): ..." for mixed lists."""
        return f"[{self.kind}] {self}"


@dataclass(frozen=True)
class LexicalError(Diagnostic):
    kind: ClassVar[str] = "error léxico"
    error_type: ClassVar[str] = "sintactico"


@dataclass(frozen=True)
class ParseError(Diagnostic):
    """(Not called SyntaxError, so it does not shadow Python's built-in.)"""

    kind: ClassVar[str] = "error sintáctico"
    error_type: ClassVar[str] = "sintactico"


@dataclass(frozen=True)
class AgreementError(Diagnostic):
    kind: ClassVar[str] = "error de concordancia"
    error_type: ClassVar[str] = "concordancia"


# Values allowed in "tipo_error" of the results (null when accepted or undecided).
ERROR_TYPES = ("sintactico", "concordancia")


def sort_by_position(diagnostics: Iterable[Diagnostic]) -> list[Diagnostic]:
    """Sentence-level diagnostics first, then by word position."""
    return sorted(diagnostics, key=lambda d: -1 if d.position is None else d.position)
