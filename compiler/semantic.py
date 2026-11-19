from .errors import CompileError, CompileWarning, SemanticError
from .statements import Statement, StatementType, group
from .symbol_table import Symbol, SymbolTable
from .tokens import Token, TokenType
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
        # Position (line, column) of every "{" not yet closed, innermost last.
        self.open_braces: list[tuple[int, int]] = []

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

        # Blocks still open at the end: one error per unclosed "{", reported
        # where that "{" is. Then close them so their unused variables are
        # still warned about.
        for line, column in self.open_braces:
            self.error("falta cerrar un bloque con '}'", line, column)
        while self.table.depth > 0:
            self.warn_unused(self.table.close_scope() or [])
        self.open_braces.clear()

        # Global scope: it is never "closed", so check it here.
        self.warn_unused(self.table.current_symbols())
        return self.errors


    def warn_unused(self, symbols: list[Symbol]) -> None:
        for symbol in symbols:
            if not symbol.used:
                self.warning(
                    f"variable '{symbol.name}' declarada pero nunca usada",
                    symbol.line,
                    symbol.column,
                )

    def open_block(self, s: Statement) -> None:
        brace = s.tokens[0]
        self.open_braces.append((brace.line, brace.column))
        self.table.open_scope()

    def close_block(self, s: Statement) -> None:
        brace = s.tokens[0]
        symbols = self.table.close_scope()
        if symbols is None:  # depth was 0: there is no block to close
            self.error("'}' sin un '{' correspondiente", brace.line, brace.column)
            return
        self.open_braces.pop()
        self.warn_unused(symbols)

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
        _ = (is_assignable, expression_type)  # used by P4's step 1
        # Undeclared variables in the initial expression are reported BEFORE
        # declaring, so `entero x = x;` flags the right-hand x.
        self.check_usage(s.expression)
        # TODO(P4): step 1 (type of s.expression and is_assignable)

        name, data_type = s.name, s.data_type
        symbol = Symbol(
            name=name.lexeme,
            type=TYPE_OF_TOKEN[data_type.type],
            line=name.line,
            column=name.column,
            initialized=bool(s.expression),
        )
        outer = self.table.lookup(symbol.name)  # BEFORE declaring
        previous = self.table.declare(symbol)
        if previous is not None:
            self.error(
                f"variable '{symbol.name}' ya declarada en este ámbito "
                f"(línea {previous.line})",
                name.line,
                name.column,
            )
            return
        self.record_declaration(symbol)
        if outer is not None:  # declared in an outer scope: shadowing
            self.warning(
                f"la variable '{symbol.name}' oculta a otra declarada "
                f"en la línea {outer.line}",
                name.line,
                name.column,
            )

    def check_usage(self, expression: list[Token]) -> None:
        """Report every ID in the expression that is not declared.

        For each declared ID, mark symbol.used = True, and if it was never
        given a value, WARNING "variable 'x' usada sin inicializar".
        """
        for token in expression:
            if token.type is not TokenType.ID:
                continue
            symbol = self.table.lookup(token.lexeme)
            if symbol is None:
                self.error(
                    f"variable '{token.lexeme}' no declarada", token.line, token.column
                )
                continue
            symbol.used = True
            if not symbol.initialized:
                self.warning(
                    f"variable '{token.lexeme}' usada sin inicializar",
                    token.line,
                    token.column,
                )

    # ------------------------------------------------------------------
    # P4: types in assignments, conditions and imprimir
    # ------------------------------------------------------------------
    def assignment(self, s: Statement) -> None:
        # The right-hand side is evaluated first: in `x = x + 1;` the x on the
        # right is read BEFORE the assignment gives it a value.
        self.check_usage(s.expression)

        name = s.name
        symbol = self.table.lookup(name.lexeme)
        if symbol is None:
            self.error(
                f"variable '{name.lexeme}' no declarada", name.line, name.column
            )
        else:
            symbol.initialized = True
        # TODO(P4): expression type vs. variable type (is_assignable).

    def condition(self, s: Statement) -> None:
        # TODO(P4): the si/mientras condition must be bool.
        raise NotImplementedError("TODO(P4): condition")

    def print_statement(self, s: Statement) -> None:
        # TODO(P4): only check that the expression is valid (any type).
        raise NotImplementedError("TODO(P4): print_statement")


def analyze(tokens: list[Token]) -> list[CompileError]:
    """Entry point used by main.py and the tests."""
    return SemanticAnalyzer().analyze(tokens)