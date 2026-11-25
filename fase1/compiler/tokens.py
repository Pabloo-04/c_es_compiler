import re
from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # --- Keywords (the language's lexemes are in Spanish) ---
    INT = auto()            # entero
    REAL = auto()           # real
    BOOL = auto()           # bool
    IF = auto()             # si
    ELSE = auto()           # sino
    WHILE = auto()          # mientras
    PRINT = auto()          # imprimir
    TRUE = auto()           # verdadero
    FALSE = auto()          # falso

    # --- Identifiers and literals ---
    ID = auto()             # [a-zA-Z_][a-zA-Z0-9_]*
    INT_LITERAL = auto()    # [0-9]+
    REAL_LITERAL = auto()   # [0-9]+\.[0-9]+

    # --- Two-character operators ---
    EQUAL = auto()          # ==
    NOT_EQUAL = auto()      # !=
    LESS_EQUAL = auto()     # <=
    GREATER_EQUAL = auto()  # >=
    AND = auto()            # &&
    OR = auto()             # ||

    # --- One-character operators ---
    PLUS = auto()           # +
    MINUS = auto()          # -
    STAR = auto()           # *
    SLASH = auto()          # /
    LESS = auto()           # <
    GREATER = auto()        # >
    ASSIGN = auto()         # =
    NOT = auto()            # !

    # --- Delimiters ---
    LPAREN = auto()         # (
    RPAREN = auto()         # )
    LBRACE = auto()         # {
    RBRACE = auto()         # }
    SEMICOLON = auto()      # ;
    COMMA = auto()          # ,

    # --- End of file ---
    EOF = auto()            # the lexer always appends one at the end


KEYWORDS: dict[str, TokenType] = {
    "entero": TokenType.INT,
    "real": TokenType.REAL,
    "bool": TokenType.BOOL,
    "si": TokenType.IF,
    "sino": TokenType.ELSE,
    "mientras": TokenType.WHILE,
    "imprimir": TokenType.PRINT,
    "verdadero": TokenType.TRUE,
    "falso": TokenType.FALSE,
}

# The lexer must try two-character operators first, so that "==" is not
# read as "=" "=".
DOUBLE_OPERATORS: dict[str, TokenType] = {
    "==": TokenType.EQUAL,
    "!=": TokenType.NOT_EQUAL,
    "<=": TokenType.LESS_EQUAL,
    ">=": TokenType.GREATER_EQUAL,
    "&&": TokenType.AND,
    "||": TokenType.OR,
}

SINGLE_OPERATORS: dict[str, TokenType] = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "<": TokenType.LESS,
    ">": TokenType.GREATER,
    "=": TokenType.ASSIGN,
    "!": TokenType.NOT,
}

DELIMITERS: dict[str, TokenType] = {
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    ";": TokenType.SEMICOLON,
    ",": TokenType.COMMA,
}

# Tokens that start a variable declaration.
DATA_TYPES = {TokenType.INT, TokenType.REAL, TokenType.BOOL}


# ======================================================================
# Formal definition: one regular expression per token type
# ======================================================================
# This is the executable version of docs/especificacion_tokens.md. The
# hand-written lexer (lexer.py) implements the same language as an
# automaton; tests/test_token_spec.py checks that both agree.
#
# Every pattern uses only non-capturing groups (?:...), so MASTER_PATTERN
# can tell which alternative matched through `match.lastindex`.

LETTER = r"[a-zA-Z_]"
DIGIT = r"[0-9]"

ID_PATTERN = rf"{LETTER}(?:{LETTER}|{DIGIT})*"
INT_PATTERN = rf"{DIGIT}+"
REAL_PATTERN = rf"{DIGIT}+\.{DIGIT}+"
WHITESPACE_PATTERN = r"[ \t\r\n]+"
LINE_COMMENT_PATTERN = r"//[^\n]*"
BLOCK_COMMENT_PATTERN = r"/\*[\s\S]*?\*/"   # lazy: ends at the FIRST "*/"

# (type, regex) in PRIORITY order. Python's `|` takes the first alternative
# that matches (not the longest), so the order encodes the disambiguation rules:
#   1. Comments before "/", so "//" and "/*" are not read as division.
#   2. REAL before INT, so "3.14" is not read as "3" "." "14".
#   3. Two-character operators before one-character ones ("==" before "=").
#   4. Keywords are NOT listed: an ID is matched first and then looked up in
#      KEYWORDS (see classify), so "enteros" is an ID and not "entero" + "s".
# A type of None means "recognize and discard" (whitespace and comments).
TOKEN_PATTERNS: list[tuple[TokenType | None, str]] = [
    (None, WHITESPACE_PATTERN),
    (None, LINE_COMMENT_PATTERN),
    (None, BLOCK_COMMENT_PATTERN),
    (TokenType.REAL_LITERAL, REAL_PATTERN),
    (TokenType.INT_LITERAL, INT_PATTERN),
    (TokenType.ID, ID_PATTERN),
    *((type_, re.escape(op)) for op, type_ in DOUBLE_OPERATORS.items()),
    *((type_, re.escape(op)) for op, type_ in SINGLE_OPERATORS.items()),
    *((type_, re.escape(d)) for d, type_ in DELIMITERS.items()),
]

# All patterns joined as (p1)|(p2)|...; group i+1 corresponds to TOKEN_PATTERNS[i].
MASTER_PATTERN = re.compile("|".join(f"({pattern})" for _, pattern in TOKEN_PATTERNS))

# NOTE: these regexes define the VALID tokens. The lexical errors "3abc" and
# "12.3.4" are an extra rule of the lexer: a number may not be immediately
# followed by a letter, "_" or another ".digits". The regexes alone would split
# "3abc" into INT_LITERAL "3" + ID "abc".


def classify(lexeme: str) -> TokenType | None:
    """Type of a COMPLETE lexeme according to the regexes, or None if it is not
    exactly one token. Whitespace and comments also give None.

        classify("si") -> IF        classify("si_") -> ID
        classify("3.14") -> REAL_LITERAL    classify("12.3.4") -> None
    """
    for type_, pattern in TOKEN_PATTERNS:
        if type_ is not None and re.fullmatch(pattern, lexeme):
            return KEYWORDS.get(lexeme, type_) if type_ is TokenType.ID else type_
    return None


@dataclass(frozen=True)
class Token:
    """A token produced by the lexer.

    - type:    token category (TokenType).
    - lexeme:  exact source text ("x", "3.14", "==").
    - line:    starts at 1.
    - column:  starts at 1; column of the FIRST character of the lexeme.
    """

    type: TokenType
    lexeme: str
    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.line}:{self.column}\t{self.type.name:<14} {self.lexeme!r}"
