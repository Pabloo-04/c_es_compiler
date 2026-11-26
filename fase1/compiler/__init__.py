"""Compiler for a C-like language with Spanish keywords (Phase 1)."""

from .errors import (
    CompileError,
    CompileWarning,
    Diagnostic,
    LexicalError,
    SemanticError,
)
from .tokens import Token, TokenType

__all__ = [
    "CompileError",
    "CompileWarning",
    "Diagnostic",
    "LexicalError",
    "SemanticError",
    "Token",
    "TokenType",
]
