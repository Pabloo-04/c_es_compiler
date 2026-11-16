"""Shared contract between the lexer (P2) and the semantic analyzer (P3 and P4).

This file is agreed on DAY 1. If anyone needs to change it, tell the whole
team first, because it breaks everyone else's work.
"""

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
