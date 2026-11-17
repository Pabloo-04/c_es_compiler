"""Semantic analyzer.  Owners: Person 3 and Person 4.

This file ORCHESTRATES the analysis: it walks the statements in order and
calls the symbol table (P3) and the type rules (P4).

To avoid Git conflicts, each person works mostly in their own file:
  - P3: symbol_table.py + the sections marked "P3" in this file.
  - P4: statements.py, type_rules.py + the sections marked "P4".

Messages (the `message` field), in Spanish, kept uniform. The position is
added by errors.py: "Línea 7, columna 3: variable 'y' no declarada".
  Errors:
  - "variable 'x' no declarada"
  - "variable 'x' ya declarada en este ámbito (línea 3)"
  - "no se puede asignar bool a entero"
  - "la condición de 'si' debe ser bool, pero es entero"
  - "operación inválida: entero && bool"
  Warnings:
  - "variable 'x' declarada pero nunca usada"
  - "la variable 'x' oculta a otra declarada en la línea 2"
  - "variable 'x' usada sin inicializar"
"""

from .errors import CompileError, CompileWarning, SemanticError
from .statements import Statement, StatementType, group
from .symbol_table import Symbol, SymbolTable
from .tokens import Token
from .type_rules import TYPE_OF_TOKEN, expression_type, is_assignable


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.table = SymbolTable()
        self.errors: list[CompileError] = []
        self.warnings: list[CompileWarning] = []
        # Every symbol ever declared, with the scope depth it was declared at.
        # Scopes are popped when a block closes, so the table alone cannot show
        # them at the end; main.py --simbolos prints this list instead.
        self.declared: list[tuple[int, Symbol]] = []

    def error(self, message: str, line: int, column: int) -> None:
        self.errors.append(SemanticError(line, column, message))

    def warning(self, message: str, line: int, column: int) -> None:
        self.warnings.append(CompileWarning(line, column, message))

    def record_declaration(self, symbol: Symbol) -> None:
        """Call right after a SUCCESSFUL table.declare(), for main.py --simbolos."""
        self.declared.append((self.table.depth, symbol))

    # ------------------------------------------------------------------
    def analyze(self, tokens: list[Token]) -> list[CompileError]:
        statements, grouping_errors = group(tokens)
        self.errors.extend(grouping_errors)

        for s in statements:
            match s.type:
                case StatementType.OPEN_BLOCK:
                    self.open_block(s)
                case StatementType.CLOSE_BLOCK:
                    self.close_block(s)
                case StatementType.DECLARATION:
                    self.declaration(s)
                case StatementType.ASSIGNMENT:
                    self.assignment(s)
                case StatementType.IF | StatementType.WHILE:
                    self.condition(s)
                case StatementType.PRINT:
                    self.print_statement(s)
                case StatementType.ELSE:
                    pass  # TODO(P4): check that it comes right after an 'si' block closes?

        # TODO(P3): if scopes are still open at the end (self.table.depth > 0),
        #           report "falta cerrar un bloque con '}'".
        # TODO(P3): WARNING "variable 'x' declarada pero nunca usada" for the
        #           global-scope symbols with used == False (inner scopes are
        #           checked in close_block).
        return self.errors

    # ------------------------------------------------------------------
    # P3: scopes and declarations
    # ------------------------------------------------------------------
    def open_block(self, s: Statement) -> None:
        # TODO(P3)
        raise NotImplementedError("TODO(P3): open_block")

    def close_block(self, s: Statement) -> None:
        # TODO(P3): report a "}" without a matching "{".
        # TODO(P3): WARNING "variable 'x' declarada pero nunca usada" for each
        #           symbol of the scope being closed with used == False.
        raise NotImplementedError("TODO(P3): close_block")

    def declaration(self, s: Statement) -> None:
        # Order matters:
        #   1) P4: type of the initial expression (if there is "=") and is_assignable.
        #      Evaluated BEFORE declaring, so `entero x = x;` flags x as undeclared.
        #   2) P3: declare in the table; if it returns a Symbol -> redeclaration.
        #      Set initialized=True when there is "=".
        #      On success, call self.record_declaration(symbol).
        #   3) P3: WARNING (shadowing) if, BEFORE declaring, lookup(name) found a
        #      symbol in an OUTER scope:
        #      "la variable 'x' oculta a otra declarada en la línea 2"
        _ = (Symbol, TYPE_OF_TOKEN, is_assignable, expression_type)
        # TODO(P4): step 1
        # TODO(P3): steps 2 and 3
        raise NotImplementedError("TODO(P3/P4): declaration")

    def check_usage(self, expression: list[Token]) -> None:
        """Report every ID in the expression that is not declared.

        TODO(P3): for each declared ID, set symbol.used = True, and if
        symbol.initialized is False, WARNING "variable 'x' usada sin inicializar".
        """
        # TODO(P3)
        raise NotImplementedError("TODO(P3): check_usage")

    # ------------------------------------------------------------------
    # P4: types in assignments, conditions and imprimir
    # ------------------------------------------------------------------
    def assignment(self, s: Statement) -> None:
        # TODO(P3): the variable on the left must be declared; then set initialized = True.
        # TODO(P4): expression type vs. variable type (is_assignable).
        raise NotImplementedError("TODO(P3/P4): assignment")

    def condition(self, s: Statement) -> None:
        # TODO(P4): the si/mientras condition must be bool.
        raise NotImplementedError("TODO(P4): condition")

    def print_statement(self, s: Statement) -> None:
        # TODO(P4): only check that the expression is valid (any type).
        raise NotImplementedError("TODO(P4): print_statement")


def analyze(tokens: list[Token]) -> list[CompileError]:
    """Entry point used by main.py and the tests."""
    return SemanticAnalyzer().analyze(tokens)
