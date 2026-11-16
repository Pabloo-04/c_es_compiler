"""Semantic analyzer.  Owners: Person 3 and Person 4.

This file ORCHESTRATES the analysis: it walks the statements in order and
calls the symbol table (P3) and the type rules (P4).

To avoid Git conflicts, each person works mostly in their own file:
  - P3: symbol_table.py + the sections marked "P3" in this file.
  - P4: statements.py, type_rules.py + the sections marked "P4".

Message format (CompileError.message), in Spanish, kept uniform:
  - "la variable 'x' no está declarada"
  - "la variable 'x' ya fue declarada en este ámbito (línea 3)"
  - "no se puede asignar bool a entero"
  - "la condición de 'si' debe ser bool, pero es entero"
  - "operación inválida: entero && bool"
"""

from .errors import CompileError, Phase
from .statements import Statement, StatementType, group
from .symbol_table import Symbol, SymbolTable
from .tokens import Token
from .type_rules import TYPE_OF_TOKEN, expression_type, is_assignable


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.table = SymbolTable()
        self.errors: list[CompileError] = []

    def error(self, message: str, line: int, column: int) -> None:
        self.errors.append(CompileError(Phase.SEMANTIC, line, column, message))

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
        return self.errors

    # ------------------------------------------------------------------
    # P3: scopes and declarations
    # ------------------------------------------------------------------
    def open_block(self, s: Statement) -> None:
        # TODO(P3)
        raise NotImplementedError("TODO(P3): open_block")

    def close_block(self, s: Statement) -> None:
        # TODO(P3): report a "}" without a matching "{".
        raise NotImplementedError("TODO(P3): close_block")

    def declaration(self, s: Statement) -> None:
        # Order matters:
        #   1) P4: type of the initial expression (if there is "=") and is_assignable.
        #      Evaluated BEFORE declaring, so `entero x = x;` flags x as undeclared.
        #   2) P3: declare in the table; if it returns a Symbol -> redeclaration.
        _ = (Symbol, TYPE_OF_TOKEN, is_assignable, expression_type)
        # TODO(P4): step 1
        # TODO(P3): step 2
        raise NotImplementedError("TODO(P3/P4): declaration")

    def check_usage(self, expression: list[Token]) -> None:
        """Report every ID in the expression that is not declared."""
        # TODO(P3)
        raise NotImplementedError("TODO(P3): check_usage")

    # ------------------------------------------------------------------
    # P4: types in assignments, conditions and imprimir
    # ------------------------------------------------------------------
    def assignment(self, s: Statement) -> None:
        # TODO(P3): the variable on the left must be declared.
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
