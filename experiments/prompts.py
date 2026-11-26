"""Prompts for the LLM experiment and parsing of its answers.  Owner: Person 5.

The production rules come from spanish/grammar.py and the words from
data/lexicon.json, so the LLM sees EXACTLY what our parser implements.

Two versions, as the assignment asks:
  - zero-shot (llm_zero): rules only.
  - few-shot  (llm_few):  rules + the solved EXAMPLES below.

The answer must be ONLY the JSON of docs/gramatica_es.md, section 2.6:

    {"acepta": true, "tipo_error": null, "etiquetas": [["ella", "Prn"], ...],
     "sujeto": "ella", "verbo": "come", "objeto": "manzana", "pp_adjunta": null,
     "arbol": "(S ...)"}

If the answer is not valid JSON, the result line gets "acepta": null and
"error_ejecucion": "respuesta_no_json" (section 2.6).

DRAFT: P5 refines the wording and the examples.
"""

import json

from spanish.grammar import TREE_SHAPES, as_bnf
from spanish.lexicon import Lexicon
from spanish.tokens import Category

REQUIRED_KEYS = ("acepta", "tipo_error", "etiquetas", "sujeto", "verbo", "objeto", "arbol")
OPTIONAL_KEYS = ("pp_adjunta",)          # missing -> None, the rest of the answer still counts
ANSWER_KEYS = REQUIRED_KEYS + OPTIONAL_KEYS

# Few-shot examples. They must NOT be sentences of the test set
# (tests/test_formats_and_prompts.py checks it). TODO(P5): review and choose
# a fixed, balanced set (accepted, agreement error, syntax error).
EXAMPLES: list[tuple[str, dict]] = [
    ("Ella duerme.", {
        "acepta": True, "tipo_error": None,
        "etiquetas": [["ella", "Prn"], ["duerme", "Verb"]],
        "sujeto": "ella", "verbo": "duerme", "objeto": "", "pp_adjunta": None,
        "arbol": "(S (NP (NPbase (Prn ella))) (VP (Verb duerme)))",
    }),
    ("La niña pequeña come una manzana roja.", {
        "acepta": True, "tipo_error": None,
        "etiquetas": [["la", "Det"], ["niña", "Noun"], ["pequeña", "Adj"], ["come", "Verb"],
                      ["una", "Det"], ["manzana", "Noun"], ["roja", "Adj"]],
        "sujeto": "niña", "verbo": "come", "objeto": "manzana", "pp_adjunta": None,
        "arbol": "(S (NP (NPbase (Det la) (Nom (Noun niña) (AdjP (Adj pequeña))))) "
                 "(VP (Verb come) (NP (NPbase (Det una) (Nom (Noun manzana) (AdjP (Adj roja)))))))",
    }),
    ("Los perro duerme.", {
        "acepta": False, "tipo_error": "concordancia",
        "etiquetas": [["los", "Det"], ["perro", "Noun"], ["duerme", "Verb"]],
        "sujeto": "perro", "verbo": "duerme", "objeto": "", "pp_adjunta": None, "arbol": None,
    }),
    ("Duerme el perro.", {
        "acepta": False, "tipo_error": "sintactico",
        "etiquetas": [["duerme", "Verb"], ["el", "Det"], ["perro", "Noun"]],
        "sujeto": "perro", "verbo": "duerme", "objeto": "", "pp_adjunta": None, "arbol": None,
    }),
    ("La niña duerme con su perro.", {
        "acepta": True, "tipo_error": None,
        "etiquetas": [["la", "Det"], ["niña", "Noun"], ["duerme", "Verb"], ["con", "Prep"],
                      ["su", "Pos"], ["perro", "Noun"]],
        "sujeto": "niña", "verbo": "duerme", "objeto": "", "pp_adjunta": "verbo",
        "arbol": "(S (NP (NPbase (Det la) (Nom (Noun niña)))) "
                 "(VP (Verb duerme) (PP (Prep con) (NP (NPbase (Pos su) (Nom (Noun perro)))))))",
    }),
]

INSTRUCTIONS = """Eres un analizador sintáctico. Usa EXCLUSIVAMENTE la gramática libre de contexto \
y el léxico que aparecen abajo, aunque conozcas otras construcciones válidas del español.

Una oración se ACEPTA solo si:
1. todas sus palabras están en el léxico y la oración se puede derivar con las reglas, y
2. dentro de cada sintagma nominal, el determinante o posesivo, el sustantivo y el adjetivo \
concuerdan en género y número (los posesivos solo en número), y el sujeto concuerda con el verbo \
en número y persona (los sustantivos son de 3.ª persona).
Si no cumple 1, el error es "sintactico"; si cumple 1 pero no 2, es "concordancia".

Gramática (S es el símbolo inicial; ε es la cadena vacía):
{grammar}

Léxico:
{lexicon}

Árbol: notación entre paréntesis. Los no terminales NP', AdjOpc, ObjOpc y VP' NO aparecen; \
sus hijos van directamente en el nodo padre. Hijos permitidos de cada nodo:
{shapes}

Responde SOLO con un objeto JSON, sin texto adicional, con estas claves:
"acepta" (true o false), "tipo_error" ("sintactico", "concordancia" o null si acepta),
"etiquetas" (lista de [palabra en minúsculas, categoría], sin el punto; usa X para palabras \
fuera del léxico), "sujeto", "verbo" y "objeto" (la palabra núcleo en minúsculas, o "" si no hay),
"pp_adjunta" (a qué se une la primera frase preposicional según la lectura de un hablante: "sustantivo",
"verbo", "ambigua" si las dos lecturas son naturales, o null si no hay frase preposicional),
"arbol" (el árbol si acepta, null si rechaza).
"""


def lexicon_text(lexicon: Lexicon | None = None) -> str:
    lexicon = lexicon or Lexicon.load()
    lines = []
    for category in Category:
        if category is Category.X:
            continue
        words = lexicon.words_by_category(category)
        if words:
            lines.append(f"{category.value:<6} → {' | '.join(words)}")
    return "\n".join(lines)


def shapes_text() -> str:
    return "\n".join(f"{label:<6} → {shape.replace('|', ' | ')}" for label, shape in TREE_SHAPES.items())


def instructions() -> str:
    # TODO(P5): decide whether to send the lexicon (rules for words) or only the
    #           phrase rules; whichever is chosen, keep it fixed for both versions.
    return INSTRUCTIONS.format(grammar=as_bnf(), lexicon=lexicon_text(), shapes=shapes_text())


def zero_shot(sentence: str) -> str:
    return instructions() + f"\nOración: {sentence}\n"


def few_shot(sentence: str, examples: list[tuple[str, dict]] = EXAMPLES) -> str:
    if any(s == sentence for s, _ in examples):
        raise ValueError("los ejemplos incluyen la oración que se pregunta")
    shots = "\n\n".join(
        f"Oración: {s}\n{json.dumps(answer, ensure_ascii=False)}" for s, answer in examples
    )
    return instructions() + "\nEjemplos resueltos:\n\n" + shots + f"\n\nOración: {sentence}\n"


def parse_answer(text: str) -> dict | None:
    """The JSON answer as a dict, or None if it is not valid JSON with the right keys.

    Strict, as the agreed format says ("solo con este JSON, sin texto adicional").
    TODO(P5): decide whether an answer wrapped in ```json ... ``` counts as valid;
              if so, strip the fences here and say it in the report.
    """
    try:
        data = json.loads(text.strip())
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or any(key not in data for key in REQUIRED_KEYS):
        return None
    if data["acepta"] not in (True, False):
        return None
    return {key: data.get(key) for key in ANSWER_KEYS}
