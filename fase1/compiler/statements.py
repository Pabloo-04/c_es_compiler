from dataclasses import dataclass, field
from enum import Enum, auto

from .errors import CompileError, SemanticError
from .tokens import DATA_TYPES, Token, TokenType


class StatementType(Enum):
    DECLARATION = auto()
    ASSIGNMENT = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    PRINT = auto()
    OPEN_BLOCK = auto()
    CLOSE_BLOCK = auto()


@dataclass
class Statement:
    type: StatementType
    tokens: list[Token]                 # every token of the statement (without the ";")
    # Handy fields already split out (None when not applicable):
    data_type: Token | None = None      # DECLARATION: the entero/real/bool token
    name: Token | None = None           # DECLARATION / ASSIGNMENT: the ID
    expression: list[Token] = field(default_factory=list)
    # ^ DECLARATION/ASSIGNMENT: what comes after "="
    #   IF/WHILE/PRINT:         what is inside the parentheses

    @property
    def line(self) -> int:
        return self.tokens[0].line


# Tokens that can only begin a statement. Finding one inside an expression
# means the previous statement ended without its ";".
STATEMENT_STARTS = DATA_TYPES | {
    TokenType.IF,
    TokenType.ELSE,
    TokenType.WHILE,
    TokenType.PRINT,
    TokenType.LBRACE,
    TokenType.RBRACE,
    TokenType.EOF,
}


class StatementGrouper:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0        # index into self.tokens
        self.statements: list[Statement] = []
        self.errors: list[CompileError] = []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def current(self) -> Token:
        """Current token. The list always ends with EOF, so past the end the
        EOF token is returned again."""
        return self.tokens[min(self.pos, len(self.tokens) - 1)]

    def peek(self) -> Token:
        """Token after the current one (1-token lookahead)."""
        return self.tokens[min(self.pos + 1, len(self.tokens) - 1)]

    def at_end(self) -> bool:
        return self.current().type is TokenType.EOF

    def advance(self) -> Token:
        """Consume the current token. EOF is never consumed."""
        token = self.current()
        if not self.at_end():
            self.pos += 1
        return token

    def check(self, type_: TokenType) -> bool:
        return self.current().type is type_

    def starts_assignment(self) -> bool:
        """`ID =` begins an assignment."""
        return self.check(TokenType.ID) and self.peek().type is TokenType.ASSIGN

    def error(self, message: str, line: int, column: int) -> None:
        self.errors.append(SemanticError(line, column, message))

    def synchronize(self) -> None:
        """Error recovery: skip tokens up to the next ";" (consumed) or up to a
        token that begins a statement, such as "{" or "}" (NOT consumed, so
        scopes still open and close)."""
        while not self.check(TokenType.SEMICOLON) and self.current().type not in STATEMENT_STARTS:
            self.advance()
        if self.check(TokenType.SEMICOLON):
            self.advance()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def analyze(self) -> tuple[list[Statement], list[CompileError]]:
        while not self.at_end():
            token = self.current()
            match token.type:
                case TokenType.LBRACE:
                    self.advance()
                    self.statements.append(Statement(StatementType.OPEN_BLOCK, [token]))
                case TokenType.RBRACE:
                    self.advance()
                    self.statements.append(Statement(StatementType.CLOSE_BLOCK, [token]))
                case TokenType.INT | TokenType.REAL | TokenType.BOOL:
                    self.read_declaration()
                case TokenType.ID:
                    self.read_assignment()
                case TokenType.IF:
                    self.read_condition(StatementType.IF)
                case TokenType.WHILE:
                    self.read_condition(StatementType.WHILE)
                case TokenType.ELSE:
                    self.advance()
                    self.statements.append(Statement(StatementType.ELSE, [token]))
                    self.expect_block(token)
                case TokenType.PRINT:
                    self.read_print()
                case _:
                    # e.g. "+ 3;": report it once and skip the rest of it.
                    self.error(f"sentencia no reconocida: '{token.lexeme}'", token.line, token.column)
                    self.advance()
                    self.synchronize()
        return self.statements, self.errors

    # ------------------------------------------------------------------
    # Recognizers (one per statement form)
    # ------------------------------------------------------------------
    def read_declaration(self) -> None:
        """type ID ;  |  type ID = expr ;"""
        start = self.pos
        data_type = self.advance()
        if not self.check(TokenType.ID):
            token = self.current()
            self.error(
                f"se esperaba un nombre de variable después de '{data_type.lexeme}'",
                token.line,
                token.column,
            )
            self.synchronize()
            return
        name = self.advance()

        expression: list[Token] = []
        if self.check(TokenType.ASSIGN):
            equals = self.advance()
            expression = self.read_expression(equals)

        end = self.pos
        self.end_statement()
        # Added even when the ";" is missing, so later uses of the variable
        # are not reported as undeclared.
        self.statements.append(Statement(
            StatementType.DECLARATION,
            self.tokens[start:end],
            data_type=data_type,
            name=name,
            expression=expression,
        ))

    def read_assignment(self) -> None:
        """ID = expr ;"""
        start = self.pos
        name = self.advance()
        if not self.check(TokenType.ASSIGN):
            token = self.current()
            self.error(f"se esperaba '=' después de '{name.lexeme}'", token.line, token.column)
            self.synchronize()
            return
        equals = self.advance()
        expression = self.read_expression(equals)

        end = self.pos
        self.end_statement()
        self.statements.append(Statement(
            StatementType.ASSIGNMENT,
            self.tokens[start:end],
            name=name,
            expression=expression,
        ))

    def read_condition(self, type_: StatementType) -> None:
        """si ( expr )  |  mientras ( expr )   -- the block is read by the main loop."""
        start = self.pos
        keyword = self.advance()
        expression = self.read_parenthesized(keyword, f"la condición de '{keyword.lexeme}'")
        if expression is None:
            # Malformed header, already reported. The statement is still added
            # (with no expression) so a following 'sino' finds its 'si'. Then
            # skip the rest of the header up to its "{".
            self.statements.append(Statement(type_, self.tokens[start:self.pos]))
            self.synchronize()
            return
        self.statements.append(Statement(type_, self.tokens[start:self.pos], expression=expression))
        self.expect_block(keyword)

    def read_print(self) -> None:
        """imprimir ( expr ) ;"""
        start = self.pos
        keyword = self.advance()
        expression = self.read_parenthesized(keyword, f"la expresión de '{keyword.lexeme}'")
        if expression is None:
            self.synchronize()
            return
        end = self.pos
        self.end_statement()
        self.statements.append(Statement(
            StatementType.PRINT,
            self.tokens[start:end],
            expression=expression,
        ))

    # ------------------------------------------------------------------
    # Pieces shared by the recognizers
    # ------------------------------------------------------------------
    def read_expression(self, equals: Token) -> list[Token]:
        """Read the expression after "=" up to the ";" (not consumed).

        It also stops before a token that begins another statement, so a
        missing ";" does not swallow the next line:
            entero x = 1        <- stops before "entero"
            entero y = 2;
        """
        expression: list[Token] = []
        while not self.check(TokenType.SEMICOLON) and not self.check(TokenType.ASSIGN):
            if self.current().type in STATEMENT_STARTS:
                break
            if expression and self.starts_assignment():
                break
            expression.append(self.advance())
        if not expression:
            self.error("falta la expresión después de '='", equals.line, equals.column)
        return expression

    def read_parenthesized(self, keyword: Token, what: str) -> list[Token] | None:
        """Read "( expr )" after si / mientras / imprimir and return what is inside.

        Nested parentheses are kept: si ((a < b) && c) -> ( a < b ) && c
        Returns None (after reporting it) if the parentheses are malformed.
        """
        if not self.check(TokenType.LPAREN):
            token = self.current()
            self.error(f"se esperaba '(' después de '{keyword.lexeme}'", token.line, token.column)
            return None
        opening = self.advance()

        expression: list[Token] = []
        depth = 1  # parentheses still open, counting the first one
        while True:
            token = self.current()
            if token.type in {TokenType.LBRACE, TokenType.RBRACE, TokenType.SEMICOLON, TokenType.EOF}:
                # Reached the block or the end of the statement without closing.
                self.error(
                    f"falta ')' para cerrar el '(' de '{keyword.lexeme}'",
                    opening.line,
                    opening.column,
                )
                return None
            if token.type is TokenType.LPAREN:
                depth += 1
            elif token.type is TokenType.RPAREN:
                depth -= 1
                if depth == 0:
                    self.advance()  # the closing ")"
                    break
            expression.append(self.advance())

        if not expression:
            self.error(f"{what} está vacía", opening.line, opening.column)
        return expression

    def end_statement(self) -> None:
        """Consume the ";" that ends a statement, or report that it is missing."""
        if self.check(TokenType.SEMICOLON):
            self.advance()
            return
        if self.current().type in STATEMENT_STARTS or self.starts_assignment():
            # The next statement already began: point just after the last
            # token of this one, where the ";" should be.
            last = self.tokens[self.pos - 1]
            self.error(
                "falta ';' al final de la sentencia",
                last.line,
                last.column + len(last.lexeme),
            )
            return
        # Something that does not belong here, e.g. "entero x 5;".
        token = self.current()
        self.error(f"se esperaba ';' en lugar de '{token.lexeme}'", token.line, token.column)
        self.synchronize()

    def expect_block(self, keyword: Token) -> None:
        """si, mientras and sino must be followed by a "{" block (not consumed:
        the main loop turns it into OPEN_BLOCK)."""
        if not self.check(TokenType.LBRACE):
            token = self.current()
            self.error(f"se esperaba '{{' después de '{keyword.lexeme}'", token.line, token.column)


def group(tokens: list[Token]) -> tuple[list[Statement], list[CompileError]]:
    """Turn the lexer's token list into a flat list of statements.

    If a statement matches no form (e.g. "x + ;" or a missing ";"), report
    a SemanticError and skip to the next ";" or "}" to keep
    analyzing (error recovery).
    """
    # The lexer always ends the list with EOF. Hand-made lists might not, and
    # the helpers rely on it to stop, so add one if it is missing.
    if not tokens or tokens[-1].type is not TokenType.EOF:
        line, column = (tokens[-1].line, tokens[-1].column + 1) if tokens else (1, 1)
        tokens = [*tokens, Token(TokenType.EOF, "", line, column)]
    return StatementGrouper(tokens).analyze()
