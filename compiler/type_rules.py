from .errors import CompileError, SemanticError
from .symbol_table import SymbolTable
from .tokens import Token, TokenType

INT = "entero"
REAL = "real"
BOOL = "bool"

NUMERIC = {INT, REAL}

# Declaration token type -> type name.
TYPE_OF_TOKEN = {
    TokenType.INT: INT,
    TokenType.REAL: REAL,
    TokenType.BOOL: BOOL,
}

# Operators grouped by the rule that gives their result type.
ARITHMETIC = {TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH}
RELATIONAL = {TokenType.LESS, TokenType.GREATER, TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL}
EQUALITY = {TokenType.EQUAL, TokenType.NOT_EQUAL}
LOGICAL = {TokenType.AND, TokenType.OR}


def binary_type(operator: TokenType, left: str, right: str) -> str | None:
    """Result type of `left operator right`, or None if invalid."""
    if operator in ARITHMETIC:
        if left in NUMERIC and right in NUMERIC:
            # Only entero with entero stays entero; any real makes it real.
            return INT if left == right == INT else REAL
        return None
    if operator in RELATIONAL:
        return BOOL if left in NUMERIC and right in NUMERIC else None
    if operator in EQUALITY:
        if (left in NUMERIC and right in NUMERIC) or left == right == BOOL:
            return BOOL
        return None
    if operator in LOGICAL:
        return BOOL if left == right == BOOL else None
    return None


def unary_type(operator: TokenType, operand: str) -> str | None:
    """Result type of `operator operand` (! or unary -), or None if invalid."""
    if operator is TokenType.NOT:
        return BOOL if operand == BOOL else None
    if operator is TokenType.MINUS:
        return operand if operand in NUMERIC else None
    return None


def is_assignable(target: str, source: str) -> bool:
    """Can a value of type `source` be stored in a variable of type `target`?"""
    # Team decision: `real x = 5;` is valid (entero -> real loses nothing),
    # `entero x = 2.5;` is not (it would lose the decimals).
    return target == source or (target == REAL and source == INT)


class ExpressionChecker:
    """Recursive descent over the tokens of ONE expression.

    One method per precedence level of docs/gramatica.md (EBNF), lowest first:
        ||   &&   == !=   < > <= >=   + -   * /   unary ! -   primary
    Every method returns the type of what it read, or None if it has an error.

    Two kinds of errors, both appended to `errors` (never raised):
      - Type errors ("operación inválida: entero && bool"): reported once; the
        None then propagates upwards WITHOUT new errors (no cascade).
      - Shape errors ("1 +", "(1", "1 2"): the first one stops the whole
        expression (self.failed), so a broken expression gives ONE error.
    """

    def __init__(
        self,
        expression: list[Token],
        table: SymbolTable,
        errors: list[CompileError],
    ) -> None:
        self.tokens = expression
        self.pos = 0        # index into self.tokens
        self.table = table
        self.errors = errors
        self.failed = False  # True after a shape error: stop reading

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def at_end(self) -> bool:
        return self.pos >= len(self.tokens)

    def current(self) -> Token | None:
        """Current token, or None at the end of the expression."""
        return None if self.at_end() else self.tokens[self.pos]

    def advance(self) -> Token:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def check(self, types: set[TokenType]) -> bool:
        token = self.current()
        return token is not None and token.type in types

    def error(self, message: str, line: int, column: int) -> None:
        self.errors.append(SemanticError(line, column, message))

    def shape_error(self, message: str, token: Token) -> None:
        """Report a malformed expression and stop reading it."""
        self.error(message, token.line, token.column)
        self.failed = True

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def analyze(self) -> str | None:
        result = self.or_expression()
        if not self.failed and not self.at_end():
            # A complete expression was read but tokens are left over: "1 2".
            token = self.current()
            self.shape_error(f"falta un operador antes de '{token.lexeme}'", token)
        return None if self.failed else result

    # ------------------------------------------------------------------
    # Precedence levels (lowest to highest)
    # ------------------------------------------------------------------
    def or_expression(self) -> str | None:
        return self.binary_level({TokenType.OR}, self.and_expression)

    def and_expression(self) -> str | None:
        return self.binary_level({TokenType.AND}, self.equality)

    def equality(self) -> str | None:
        return self.binary_level(EQUALITY, self.relational)

    def relational(self) -> str | None:
        return self.binary_level(RELATIONAL, self.additive)

    def additive(self) -> str | None:
        return self.binary_level({TokenType.PLUS, TokenType.MINUS}, self.multiplicative)

    def multiplicative(self) -> str | None:
        return self.binary_level({TokenType.STAR, TokenType.SLASH}, self.unary)

    def binary_level(self, operators: set[TokenType], next_level) -> str | None:
        """One EBNF rule `next { op next }`: the loop gives left associativity,
        so `a - b - c` is checked as `(a - b) - c`."""
        left = next_level()
        while not self.failed and self.check(operators):
            operator = self.advance()
            right = next_level()
            if left is None or right is None:
                left = None  # already reported (or undeclared): no cascade
                continue
            result = binary_type(operator.type, left, right)
            if result is None:
                self.error(
                    f"operación inválida: {left} {operator.lexeme} {right}",
                    operator.line,
                    operator.column,
                )
            left = result
        return left

    def unary(self) -> str | None:
        """`! unary | - unary | primary`. Recursive, so it is right associative: `!!b`."""
        if not self.check({TokenType.NOT, TokenType.MINUS}):
            return self.primary()
        operator = self.advance()
        operand = self.unary()
        if operand is None:
            return None
        result = unary_type(operator.type, operand)
        if result is None:
            self.error(
                f"operación inválida: {operator.lexeme}{operand}",
                operator.line,
                operator.column,
            )
        return result

    def primary(self) -> str | None:
        token = self.current()
        if token is None:
            # The expression ended where a value was expected: "1 +".
            # An expression with no tokens at all was already reported by
            # statements.group(), so there is nothing to point at here.
            if self.pos == 0:
                self.failed = True
            else:
                previous = self.tokens[self.pos - 1]
                self.shape_error(f"expresión incompleta después de '{previous.lexeme}'", previous)
            return None

        match token.type:
            case TokenType.INT_LITERAL:
                self.advance()
                return INT
            case TokenType.REAL_LITERAL:
                self.advance()
                return REAL
            case TokenType.TRUE | TokenType.FALSE:
                self.advance()
                return BOOL
            case TokenType.ID:
                self.advance()
                # If it is missing, check_usage (P3) already said "no declarada".
                symbol = self.table.lookup(token.lexeme)
                return None if symbol is None else symbol.type
            case TokenType.LPAREN:
                return self.parenthesized()
            case _:
                self.shape_error(f"se esperaba un valor en lugar de '{token.lexeme}'", token)
                return None

    def parenthesized(self) -> str | None:
        """`( expression )`: the parentheses only group, the type is the inner one."""
        opening = self.advance()
        inner = self.or_expression()
        if self.failed:
            return None
        if self.at_end():
            self.shape_error("falta ')' para cerrar el '('", opening)
            return None
        if not self.check({TokenType.RPAREN}):
            token = self.current()
            self.shape_error(f"se esperaba ')' en lugar de '{token.lexeme}'", token)
            return None
        self.advance()
        return inner


def expression_type(
    expression: list[Token],
    table: SymbolTable,
    errors: list[CompileError],
) -> str | None:
    """Compute the type of an expression (a list of tokens).

    - Literals: INT_LITERAL -> entero, REAL_LITERAL -> real, verdadero/falso -> bool.
    - ID: look it up in the table. If it is missing, the "not declared" error
      is added by P3 (see SemanticAnalyzer.check_usage); just return None here.
    - Return None if the expression has a type error (and append the error).
      If a subexpression is already None, propagate None WITHOUT adding more
      errors (avoids a cascade of messages for a single problem).

    Precedence (lowest to highest):  ||   &&   == !=   < > <= >=   + -   * /   unary ! -
    Implemented by ExpressionChecker (recursive descent, one method per level).
    """
    return ExpressionChecker(expression, table, errors).analyze()
