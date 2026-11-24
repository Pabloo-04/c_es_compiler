"""Prompts for the LLM experiment and parsing of its answers.  Owner: Person 5.

The production rules come from spanish/grammar.py (as_bnf), so the LLM sees
EXACTLY the grammar our parser implements.

Two versions, as the assignment asks:
  - zero-shot: rules only.
  - few-shot:  rules + solved examples (taken from the test set, but NEVER the
               sentence being asked: that would leak the answer).

The answer format is fixed so it can be parsed automatically:

    ACEPTADA: sí | no
    ARBOL: (O (SN ...) (SV ...))      (only if accepted)
    ERROR: concordancia | sintactico | lexico   (only if rejected)
    EXPLICACION: one line

DRAFT: P5 refines the wording; keep the answer format in sync with parse_answer().
"""

import re

from evaluation.formats import TestItem
from spanish.grammar import as_bnf

INSTRUCTIONS = """Eres un analizador sintáctico. Usa EXCLUSIVAMENTE la gramática libre de contexto \
que aparece abajo, aunque conozcas otras construcciones válidas del español.

Una oración se ACEPTA solo si:
1. se puede derivar con estas reglas, y
2. el determinante, el sustantivo y el adjetivo concuerdan en género y número, y el sujeto \
concuerda con el verbo en número y persona.

Gramática:
{grammar}

Responde EXACTAMENTE con este formato, sin texto adicional:
ACEPTADA: sí | no
ARBOL: <árbol entre paréntesis, solo si se acepta, p. ej. (O (SN (DET el) (SUST gato)) (SV (V come)))>
ERROR: <concordancia | sintactico | lexico, solo si se rechaza>
EXPLICACION: <una línea>
"""


def zero_shot(sentence: str) -> str:
    return INSTRUCTIONS.format(grammar=as_bnf()) + f"\nOración: {sentence}\n"


def few_shot(sentence: str, examples: list[TestItem]) -> str:
    """`examples` must NOT include the sentence being asked."""
    if any(e.sentence == sentence for e in examples):
        raise ValueError("el ejemplo incluye la oración que se pregunta")
    shots = "\n\n".join(format_example(e) for e in examples)
    return (
        INSTRUCTIONS.format(grammar=as_bnf())
        + "\nEjemplos resueltos:\n\n"
        + shots
        + f"\n\nOración: {sentence}\n"
    )


def format_example(item: TestItem) -> str:
    """A test item written as a solved example in the answer format."""
    lines = [f"Oración: {item.sentence}"]
    if item.covered:
        lines += ["ACEPTADA: sí", f"ARBOL: {item.tree}"]
    else:
        lines += ["ACEPTADA: no", f"ERROR: {item.error_type}"]
    # TODO(P5): add an EXPLICACION line to the examples? (it may help or bias the model)
    return "\n".join(lines)


def parse_answer(text: str) -> dict:
    """Extract the fields of an answer. Missing or malformed fields come back as None.

    Returns {"aceptada": bool | None, "arbol": str | None,
             "tipo_error": str | None, "explicacion": str | None,
             "formato_valido": bool}
    """
    def field_value(name: str) -> str | None:
        match = re.search(rf"^\s*{name}\s*:\s*(.+?)\s*$", text, flags=re.IGNORECASE | re.MULTILINE)
        return match.group(1) if match else None

    accepted_text = (field_value("ACEPTADA") or "").lower()
    accepted = {"sí": True, "si": True, "no": False}.get(accepted_text)
    error = field_value("ERROR")
    result = {
        "aceptada": accepted,
        "arbol": field_value("ARBOL"),
        "tipo_error": error.lower() if error else None,
        "explicacion": field_value("EXPLICACION"),
    }
    result["formato_valido"] = accepted is not None and (
        result["arbol"] is not None if accepted else result["tipo_error"] is not None
    )
    return result
