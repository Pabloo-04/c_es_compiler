"""Symbol table as a stack of scopes.  Owner: Person 3.

- The stack starts with ONE scope: the global one.
- "{" opens a new scope (push) and "}" closes it (pop).
- declare() looks ONLY at the current scope (top of the stack):
  if the name already exists there -> redeclaration.
- lookup() walks the stack from the top down to the global scope:
  that is how shadowing works (the innermost declaration wins).

Valid shadowing example:
    entero x = 1;
    si (verdadero) {
        real x = 2.5;   // OK: different scope, hides the outer x
    }
    entero x = 3;       // ERROR: redeclaration in the same scope
"""

from dataclasses import dataclass


@dataclass
class Symbol:
    name: str
    type: str          # "entero", "real" or "bool" (see type_rules.py)
    line: int          # where it was declared (useful for the redeclaration message)
    column: int


class SymbolTable:
    def __init__(self) -> None:
        # TODO(P3): choose the structure. Suggestion: a list of dicts.
        #   self._scopes: list[dict[str, Symbol]] = [{}]
        raise NotImplementedError("TODO(P3): SymbolTable.__init__")

    @property
    def depth(self) -> int:
        """0 = global, 1 = inside one block, and so on."""
        # TODO(P3)
        raise NotImplementedError("TODO(P3): depth")

    def open_scope(self) -> None:
        # TODO(P3)
        raise NotImplementedError("TODO(P3): open_scope")

    def close_scope(self) -> None:
        # TODO(P3): what if someone tries to close the global scope (an extra "}")?
        #           Suggestion: do not pop, and let semantic.py report the error.
        raise NotImplementedError("TODO(P3): close_scope")

    def declare(self, symbol: Symbol) -> Symbol | None:
        """Declare in the current scope.

        Returns None on success, or the Symbol ALREADY in this scope if it is
        a redeclaration (so the message can say where it was declared).
        """
        # TODO(P3)
        raise NotImplementedError("TODO(P3): declare")

    def lookup(self, name: str) -> Symbol | None:
        """Search from the innermost scope out to the global one. None if missing."""
        # TODO(P3)
        raise NotImplementedError("TODO(P3): lookup")

    def __str__(self) -> str:
        """Readable dump of the stack, useful for the video demo."""
        # TODO(P3): e.g.
        #   [depth 1] x: real (line 3)
        #   [depth 0] x: entero (line 1), y: bool (line 2)
        return super().__str__()
