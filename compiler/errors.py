"""Common error format for every phase.

Team decision: phases do NOT stop at the first error. They collect every
error in a list and keep analyzing.

The messages the user sees are in Spanish, as the assignment requires:
    "Línea 7: no se puede asignar bool a entero"
"""

from dataclasses import dataclass
from enum import Enum


class Phase(Enum):
    LEXICAL = "léxico"
    SEMANTIC = "semántico"


@dataclass(frozen=True)
class CompileError:
    phase: Phase
    line: int
    column: int
    message: str  # just the cause, without "Línea N:", e.g. "no se puede asignar bool a entero"

    def __str__(self) -> str:
        return f"Línea {self.line}: {self.message}"

    def detailed(self) -> str:
        return f"[{self.phase.value}] Línea {self.line}, columna {self.column}: {self.message}"
