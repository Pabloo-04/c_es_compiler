from dataclasses import dataclass

@dataclass
class Symbol:
    name: str
    type: str          # "entero", "real" or "bool" (see type_rules.py)
    line: int          # where it was declared (useful for the redeclaration message)
    column: int
    initialized: bool = False  # True once it gets a value (declared with "=" or assigned)
    used: bool = False         # True once it appears in an expression (for warnings)


class SymbolTable:
    def __init__(self) -> None:
        # Stack of scopes: index 0 is the global scope, the last one is the
        # current (innermost) scope. dicts keep insertion order, so symbols
        # always come out in declaration order.
        self._scopes: list[dict[str, Symbol]] = [{}]

    @property
    def depth(self) -> int:
        """0 = global, 1 = inside one block, and so on."""
        return len(self._scopes) - 1

    def open_scope(self) -> None:
        self._scopes.append({})

    def close_scope(self) -> list[Symbol] | None:
        """Pop the innermost scope and return its symbols (declaration order).

        The global scope is never popped: if someone tries to close it (an
        extra "}"), nothing changes and None is returned, so semantic.py can
        report the error.
        """
        if self.depth == 0:
            return None
        return list(self._scopes.pop().values())

    def current_symbols(self) -> list[Symbol]:
        """Symbols of the innermost scope only, in declaration order."""
        return list(self._scopes[-1].values())

    def declare(self, symbol: Symbol) -> Symbol | None:
        """Declare in the current scope.

        Returns None on success, or the Symbol ALREADY in this scope if it is
        a redeclaration (so the message can say where it was declared).
        The existing symbol is kept; the new one is NOT stored.
        """
        current = self._scopes[-1]
        previous = current.get(symbol.name)
        if previous is not None:
            return previous
        current[symbol.name] = symbol
        return None

    def lookup(self, name: str) -> Symbol | None:
        """Search from the innermost scope out to the global one. None if missing."""
        for scope in reversed(self._scopes):
            symbol = scope.get(name)
            if symbol is not None:
                return symbol
        return None

    def __str__(self) -> str:
        """Readable dump of the stack, innermost scope first, e.g.:

            [depth 1] x: real (line 3)
            [depth 0] x: entero (line 1), y: bool (line 2)
        """
        lines = []
        for depth in range(self.depth, -1, -1):
            symbols = ", ".join(
                f"{s.name}: {s.type} (line {s.line})"
                for s in self._scopes[depth].values()
            )
            lines.append(f"[depth {depth}] {symbols}".rstrip())
        return "\n".join(lines)