"""Shared contract: the syntax tree.

Produced by the parser (P2), checked by agreement.py (P3), drawn by trees.py
(P3), and compared by the metrics (P4) through its bracketed form:

    (O (SN (DET el) (SUST gato)) (SV (V come)))

The bracketed form is ALSO the format in which spaCy/Transformers results and
the LLM answers are written (docs/formato_salida.md), so every system can be
compared with the same string. Node.from_bracketed() reads it back.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass, field

from .tokens import Reading, Token


@dataclass
class Node:
    """A node of the tree.

    - Phrase node:  label "SN", children = sub-nodes, token None.
    - Leaf node:    label = lexical category ("DET", "SUST"...), no children,
                    word = the word, token/reading = what the parser chose
                    (None when the tree was read from a string).
    """

    label: str
    children: list["Node"] = field(default_factory=list)
    word: str | None = None
    token: Token | None = None
    reading: Reading | None = None

    # ------------------------------------------------------------------
    @classmethod
    def leaf(cls, token: Token, reading: Reading) -> "Node":
        """Leaf for a word with the reading the parser selected."""
        return cls(reading.category.value, word=token.word, token=token, reading=reading)

    @property
    def is_leaf(self) -> bool:
        return self.word is not None

    def leaves(self) -> list["Node"]:
        """Leaf nodes, left to right (the words of the sentence)."""
        if self.is_leaf:
            return [self]
        return [leaf for child in self.children for leaf in child.leaves()]

    def walk(self) -> Iterator["Node"]:
        """Every node, pre-order (parent before children)."""
        yield self
        for child in self.children:
            yield from child.walk()

    def find_all(self, label: str) -> list["Node"]:
        """Every node with this label, e.g. tree.find_all("SN")."""
        return [node for node in self.walk() if node.label == label]

    def child(self, label: str) -> "Node | None":
        """First DIRECT child with this label, or None."""
        return next((c for c in self.children if c.label == label), None)

    # ------------------------------------------------------------------
    def to_bracketed(self) -> str:
        """"(O (SN (DET el) (SUST gato)) (SV (V come)))"."""
        if self.is_leaf:
            return f"({self.label} {self.word})"
        inner = " ".join(child.to_bracketed() for child in self.children)
        return f"({self.label} {inner})"

    def pretty(self, indent: str = "  ") -> str:
        """Multi-line indented form, for the terminal demo."""
        lines: list[str] = []

        def visit(node: "Node", depth: int) -> None:
            pad = indent * depth
            if node.is_leaf:
                lines.append(f"{pad}{node.label} {node.word}")
            else:
                lines.append(f"{pad}{node.label}")
                for child in node.children:
                    visit(child, depth + 1)

        visit(self, 0)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.to_bracketed()

    # ------------------------------------------------------------------
    @classmethod
    def from_bracketed(cls, text: str) -> "Node":
        """Parse "(O (SN (DET el) (SUST gato)) (SV (V come)))".

        Raises ValueError if the text is not a single well-formed tree. Leaves
        come back without token/reading (only label and word).
        """
        items = re.findall(r"\(|\)|[^\s()]+", text)
        if not items:
            raise ValueError("árbol vacío")
        pos = 0

        def parse() -> Node:
            nonlocal pos
            if pos >= len(items) or items[pos] != "(":
                raise ValueError(f"se esperaba '(' en la posición {pos}")
            pos += 1
            if pos >= len(items) or items[pos] in "()":
                raise ValueError("falta la etiqueta del nodo")
            label = items[pos]
            pos += 1
            # Leaf: (LABEL word)
            if pos + 1 < len(items) and items[pos] not in "()" and items[pos + 1] == ")":
                node = cls(label, word=items[pos])
                pos += 2
                return node
            children = []
            while pos < len(items) and items[pos] == "(":
                children.append(parse())
            if pos >= len(items) or items[pos] != ")":
                raise ValueError(f"se esperaba ')' después del nodo {label}")
            if not children:
                raise ValueError(f"el nodo {label} no tiene hijos ni palabra")
            pos += 1
            return cls(label, children)

        tree = parse()
        if pos != len(items):
            raise ValueError("sobra texto después del árbol")
        return tree


def same_tree(a: str | Node | None, b: str | Node | None) -> bool:
    """Structural equality (labels and words) of two trees or bracketed strings.

    Whitespace and the case of the WORDS do not matter ("El" == "el": the
    sentence may start with a capital letter); labels must match exactly.
    Two None count as equal. A malformed string raises ValueError.
    """
    if a is None or b is None:
        return a is None and b is None
    a_node = Node.from_bracketed(a) if isinstance(a, str) else a
    b_node = Node.from_bracketed(b) if isinstance(b, str) else b
    return _normalized(a_node) == _normalized(b_node)


def _normalized(node: Node) -> str:
    if node.is_leaf:
        return f"({node.label} {node.word.lower()})"
    return f"({node.label} " + " ".join(_normalized(c) for c in node.children) + ")"
