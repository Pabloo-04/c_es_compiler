"""Lexical analyzer.  Owner: Person 2.

Input:  the source code as a string.
Output: (tokens, errors)
  - tokens: list of Token, ALWAYS ending with an EOF token.
  - errors: list of LexicalError (empty if all is fine).

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

Team decisions implemented here (confirm with P1 so the docs match):
  - "12." (a dot with no digits after it) is a malformed number.
  - ".5" is NOT a number: "." is an invalid character and then 5 is read.
  - Letters are ASCII only ([a-zA-Z_]), as in docs/especificacion_tokens.md.
  - A malformed lexeme is consumed whole and reported with ONE error.
"""

from .errors import CompileError, LexicalError
from .tokens import (
    DELIMITERS,
    DOUBLE_OPERATORS,
    KEYWORDS,
    SINGLE_OPERATORS,
    Token,
    TokenType,
)


def is_digit(c: str) -> bool:
    # NOTE: do not use `c in "0123456789"`: it is True for the empty string "".
    return len(c) == 1 and "0" <= c <= "9"


def is_letter(c: str) -> bool:
    return len(c) == 1 and (("a" <= c <= "z") or ("A" <= c <= "Z") or c == "_")


def is_word_char(c: str) -> bool:
    return is_letter(c) or is_digit(c)


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
        self.errors.append(LexicalError(line, column, message))

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def analyze(self) -> tuple[list[Token], list[CompileError]]:
        while not self.at_end():
            c = self.current()
            line, column = self.line, self.column  # start position of the lexeme

            # Whitespace: skip it, no token.
            if c in " \t\r\n":
                self.advance()
                continue

            # Comments. Must be checked BEFORE the "/" operator.
            if c == "/" and self.peek() == "/":
                self.skip_line_comment()
                continue
            if c == "/" and self.peek() == "*":
                self.skip_block_comment(line, column)
                continue

            # Identifier or keyword.
            if is_letter(c):
                self.read_identifier(line, column)
                continue

            # Number (or a malformed number such as 3abc or 12.3.4).
            if is_digit(c):
                self.read_number(line, column)
                continue

            # Two-character operators first (maximal munch): "==" is not "=" "=".
            pair = c + self.peek()
            if pair in DOUBLE_OPERATORS:
                self.advance()
                self.advance()
                self.add_token(DOUBLE_OPERATORS[pair], pair, line, column)
                continue

            # One-character operators and delimiters.
            if c in SINGLE_OPERATORS:
                self.advance()
                self.add_token(SINGLE_OPERATORS[c], c, line, column)
                continue
            if c in DELIMITERS:
                self.advance()
                self.add_token(DELIMITERS[c], c, line, column)
                continue

            # Anything else (@ # $ a lone & or |, ".", ...): report it and move on.
            # advance() guarantees progress, so there is no infinite loop.
            self.error(f"carácter inválido '{c}'", line, column)
            self.advance()

        self.add_token(TokenType.EOF, "", self.line, self.column)
        return self.tokens, self.errors

    # ------------------------------------------------------------------
    # Recognizers (one per initial state of the automaton)
    # ------------------------------------------------------------------
    def read_identifier(self, line: int, column: int) -> None:
        """Read [a-zA-Z_][a-zA-Z0-9_]* and decide whether it is an ID or a keyword."""
        chars = []
        while is_word_char(self.current()):
            chars.append(self.advance())
        lexeme = "".join(chars)
        # The full identifier is read first, so "enteros" is an ID, not "entero" + "s".
        type_ = KEYWORDS.get(lexeme, TokenType.ID)
        self.add_token(type_, lexeme, line, column)

    def read_number(self, line: int, column: int) -> None:
        """Read INT_LITERAL ([0-9]+) or REAL_LITERAL ([0-9]+\\.[0-9]+).

        Error cases (the whole malformed lexeme is consumed, ONE error is reported):
          - "12.3.4": another "." followed by digits after a real.
          - "3abc":   a number immediately followed by a letter or "_".
          - "12.":    a dot with no digits after it.
        """
        chars = []
        while is_digit(self.current()):
            chars.append(self.advance())
        type_ = TokenType.INT_LITERAL

        if self.current() == ".":
            if is_digit(self.peek()):
                # Fractional part: [0-9]+ "." [0-9]+
                chars.append(self.advance())            # the "."
                while is_digit(self.current()):
                    chars.append(self.advance())
                type_ = TokenType.REAL_LITERAL
            else:
                # "12." -> dot with nothing after it.
                chars.append(self.advance())
                self.error(f"número mal formado '{''.join(chars)}'", line, column)
                return

        # Malformed: a second "." with digits ("12.3.4") or a letter/underscore
        # glued to the number ("3abc", "3.5x"). Swallow the rest of the lexeme.
        if (self.current() == "." and is_digit(self.peek())) or is_letter(self.current()):
            while is_word_char(self.current()) or (self.current() == "." and is_digit(self.peek())):
                chars.append(self.advance())
            lexeme = "".join(chars)
            if "." in lexeme:
                self.error(f"número mal formado '{lexeme}'", line, column)
            else:
                self.error(f"identificador no puede empezar con dígito: '{lexeme}'", line, column)
            return

        self.add_token(type_, "".join(chars), line, column)

    def skip_line_comment(self) -> None:
        # Advance until "\n" or end of input; the "\n" itself is left for the main loop.
        while not self.at_end() and self.current() != "\n":
            self.advance()

    def skip_block_comment(self, line: int, column: int) -> None:
        """Skip /* ... */. If the input ends without "*/", report
        "comentario sin cerrar" at the line and column where it started."""
        self.advance()  # "/"
        self.advance()  # "*"
        while not self.at_end():
            if self.current() == "*" and self.peek() == "/":
                self.advance()
                self.advance()
                return
            self.advance()
        self.error("comentario sin cerrar", line, column)


def tokenize(source: str) -> tuple[list[Token], list[CompileError]]:
    """Entry point used by main.py and the tests."""
    return Lexer(source).analyze()