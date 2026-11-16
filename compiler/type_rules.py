"""Type rules.  Owner: Person 4.

(Named type_rules.py and not types.py so it never shadows Python's
standard `types` module.)

Language types: "entero", "real", "bool".
They are plain strings so error messages come out directly in Spanish:
    "no se puede asignar bool a entero"

Minimum required rules:
  - entero x = verdadero;          -> error
  - entero + real                  -> real
  - si / mientras condition        -> must be bool

Suggested table (complete / confirm with the team):
  arithmetic  + - * /     entero,entero -> entero
                          entero,real | real,entero | real,real -> real
                          anything with bool -> error
  relational  < > <= >=   numeric -> bool
  equality    == !=       same type (or entero/real) -> bool
  logical     && ||       bool,bool -> bool
  unary       !           bool -> bool
              -           entero -> entero, real -> real
"""

from .errors import CompileError
from .symbol_table import SymbolTable
from .tokens import Token, TokenType

INT = "entero"
REAL = "real"
BOOL = "bool"

# Declaration token type -> type name.
TYPE_OF_TOKEN = {
    TokenType.INT: INT,
    TokenType.REAL: REAL,
    TokenType.BOOL: BOOL,
}


def binary_type(operator: TokenType, left: str, right: str) -> str | None:
    """Result type of `left operator right`, or None if invalid."""
    # TODO(P4): implement the table above.
    raise NotImplementedError("TODO(P4): binary_type")


def unary_type(operator: TokenType, operand: str) -> str | None:
    # TODO(P4)
    raise NotImplementedError("TODO(P4): unary_type")


def is_assignable(target: str, source: str) -> bool:
    """Can a value of type `source` be stored in a variable of type `target`?"""
    # TODO(P4): same type -> True.
    # TODO(team): is `real x = 5;` allowed (entero -> real)? Usually YES.
    #             And `entero x = 2.5;`? Usually NO.
    raise NotImplementedError("TODO(P4): is_assignable")


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
    Suggestion: recursive descent, one function per precedence level,
    sharing an index over `expression`.
    """
    # TODO(P4)
    raise NotImplementedError("TODO(P4): expression_type")
