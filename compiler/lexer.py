"""Lexical analyzer.  Owner: Person 2.

Input:  the source code as a string.
Output: (tokens, errors)
  - tokens: list of Token, ALWAYS ending with an EOF token.
  - errors: list of CompileError with phase LEXICAL (empty if all is fine).

Rules (see docs/especificacion_tokens.md):
  - Whitespace and comments (// and /* */) are skipped.
  - Keywords are recognized AFTER reading a full identifier
    (look the lexeme up in KEYWORDS).
  - On an error, report it and keep going (do not raise).

Lexical errors to report (messages in Spanish):
  - Invalid character, e.g. "@", "#", "$", or a lone "&" / "|".
  - Malformed number: "12.3.4"
  - Identifier starting with a digit: "3abc"
  - Unterminated block comment: "/* ..." up to end of file.
"""

from .errors import CompileError, Phase
from .tokens import (
    DELIMITERS,
    DOUBLE_OPERATORS,
    KEYWORDS,
    SINGLE_OPERATORS,
    Token,
    TokenType,
)


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0        # index into self.source
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []
        self.errors: list[CompileError] = []

    # ------------------------------------------------------------------
    # Helpers (already implemented)
    # ------------------------------------------------------------------
    def at_end(self) -> bool:
        return self.pos >= len(self.source)

    def current(self) -> str:
        """Current character, or "" at end of input."""
        return "" if self.at_end() else self.source[self.pos]

    def peek(self) -> str:
        """Character after the current one (1-char lookahead), or "" if none."""
        i = self.pos + 1
        return self.source[i] if i < len(self.source) else ""

    def advance(self) -> str:
        """Consume one character and update line and column."""
        c = self.source[self.pos]
        self.pos += 1
        if c == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return c

    def add_token(self, type_: TokenType, lexeme: str, line: int, column: int) -> None:
        self.tokens.append(Token(type_, lexeme, line, column))

    def error(self, message: str, line: int, column: int) -> None:
        self.errors.append(CompileError(Phase.LEXICAL, line, column, message))

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def analyze(self) -> tuple[list[Token], list[CompileError]]:
        while not self.at_end():
            c = self.current()
            line, column = self.line, self.column  # start position of the lexeme

            # TODO(P2): whitespace -> advance without producing a token.

            # TODO(P2): comments.
            #   "//" -> skip to end of line (call self.skip_line_comment()).
            #   "/*" -> call self.skip_block_comment(line, column).
            #   NOTE: check this BEFORE the "/" operator.

            # TODO(P2): letter or "_" -> self.read_identifier(line, column).

            # TODO(P2): digit -> self.read_number(line, column).

            # TODO(P2): two-character operators (c + self.peek() in DOUBLE_OPERATORS),
            #           then single operators and delimiters.

            # TODO(P2): anything else -> self.error(f"carácter inválido '{c}'", ...)
            #           and advance, to avoid an infinite loop.
            raise NotImplementedError("TODO(P2): implement Lexer.analyze")

        self.add_token(TokenType.EOF, "", self.line, self.column)
        return self.tokens, self.errors

    # ------------------------------------------------------------------
    # Recognizers (one per initial state of the automaton)
    # ------------------------------------------------------------------
    def read_identifier(self, line: int, column: int) -> None:
        """Read [a-zA-Z_][a-zA-Z0-9_]* and decide whether it is an ID or a keyword."""
        # TODO(P2): consume while letter, digit or "_".
        # TODO(P2): type_ = KEYWORDS.get(lexeme, TokenType.ID)
        raise NotImplementedError("TODO(P2): read_identifier")

    def read_number(self, line: int, column: int) -> None:
        """Read INT_LITERAL ([0-9]+) or REAL_LITERAL ([0-9]+\\.[0-9]+).

        Error cases:
          - "12.3.4": another "." followed by digits after a real.
          - "3abc":   a number immediately followed by a letter or "_".
          - "12."     (dot with no digits after it): TODO(team) decide if it is an error.
        Suggestion: on error, consume the whole malformed lexeme and report
        ONE error with it, e.g. "número mal formado '12.3.4'".
        """
        # TODO(P2)
        raise NotImplementedError("TODO(P2): read_number")

    def skip_line_comment(self) -> None:
        # TODO(P2): advance until "\n" or end of input (leaving the "\n" is fine).
        raise NotImplementedError("TODO(P2): skip_line_comment")

    def skip_block_comment(self, line: int, column: int) -> None:
        """Skip /* ... */. If the input ends without "*/", report
        "comentario sin cerrar" at the line and column where it started."""
        # TODO(P2)
        raise NotImplementedError("TODO(P2): skip_block_comment")


def tokenize(source: str) -> tuple[list[Token], list[CompileError]]:
    """Entry point used by main.py and the tests."""
    return Lexer(source).analyze()
