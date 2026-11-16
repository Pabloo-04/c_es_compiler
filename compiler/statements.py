"""Grouping tokens into statements.  Owner: Person 4.

There is no full parser in this phase. The assignment allows a simple
representation: a FLAT list of statements, where braces are also
"statements" (OPEN_BLOCK / CLOSE_BLOCK). That way the semantic analyzer
can open and close scopes by walking the list in order.

Recognized forms:
    DECLARATION   type ID ;              |  type ID = expr ;
    ASSIGNMENT    ID = expr ;
    IF            si ( expr )            (the "{" that follows is its own statement)
    ELSE          sino
    WHILE         mientras ( expr )
    PRINT         imprimir ( expr ) ;
    OPEN_BLOCK    {
    CLOSE_BLOCK   }

Example:
    entero x = 1;            -> DECLARATION
    si (x > 0) {             -> IF, OPEN_BLOCK
        x = x + 1;           -> ASSIGNMENT
    } sino {                 -> CLOSE_BLOCK, ELSE, OPEN_BLOCK
        imprimir(x);         -> PRINT
    }                        -> CLOSE_BLOCK
"""

from dataclasses import dataclass, field
from enum import Enum, auto

from .errors import CompileError
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


def group(tokens: list[Token]) -> tuple[list[Statement], list[CompileError]]:
    """Turn the lexer's token list into a flat list of statements.

    If a statement matches no form (e.g. "x + ;" or a missing ";"), report
    an error with phase SEMANTIC and skip to the next ";" or "}" to keep
    analyzing (error recovery).
    """
    # TODO(P4): walk the tokens with an index i, ignoring the EOF token.
    #   - LBRACE / RBRACE           -> OPEN_BLOCK / CLOSE_BLOCK
    #   - token in DATA_TYPES       -> DECLARATION (read up to ";")
    #   - ID followed by ASSIGN     -> ASSIGNMENT (read up to ";")
    #   - IF / WHILE                -> read "(" expr ")" with balanced parentheses
    #   - ELSE                      -> ELSE
    #   - PRINT                     -> read "(" expr ")" ";"
    # TODO(P4): helper to extract what is between parentheses, honoring
    #           nested parentheses: si ((a < b) && c)
    _ = (DATA_TYPES, TokenType)  # used by the implementation
    raise NotImplementedError("TODO(P4): group")
