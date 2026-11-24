# Formato del set de prueba y de los resultados

**Responsables:** Persona 1 y Persona 4 (propuesta; confirmar antes de llenar el set de prueba)

Todos los sistemas (nuestro parser, spaCy, Transformers y el LLM) escriben sus resultados
en el mismo formato. Así las métricas (`evaluation/metrics.py`) se calculan igual para todos.
La implementación está en [evaluation/formats.py](../evaluation/formats.py), que además
valida cada línea al cargarla.

Los archivos son **JSON Lines** (`.jsonl`): un objeto JSON por línea. Se pueden abrir con
cualquier editor y con `pandas.read_json(path, lines=True)`.

## Set de prueba: `data/test_set.jsonl`

```json
{"id": "S006", "nivel": "compleja", "oracion": "la niña pequeña lee un libro en la casa",
 "gramatical": true, "cubierta": true,
 "arbol": "(O (SN (DET la) (SUST niña) (SA (ADJ pequeña))) (SV (V lee) (SN (DET un) (SUST libro)) (SP (PREP en) (SN (DET la) (SUST casa)))))",
 "tipo_error": null, "notas": ""}
```

| Campo | Tipo | Significado |
| --- | --- | --- |
| `id` | texto | Identificador único (`S001`, `S002`…). |
| `nivel` | `simple` \| `intermedia` \| `compleja` | Dificultad. |
| `oracion` | texto | La oración. |
| `gramatical` | booleano | ¿Es español correcto, según un hablante nativo? |
| `cubierta` | booleano | ¿Nuestra gramática **debe** aceptarla? |
| `arbol` | texto o `null` | Árbol esperado, entre paréntesis. Obligatorio si `cubierta`. |
| `tipo_error` | `lexico` \| `sintactico` \| `concordancia` \| `null` | Por qué se rechaza. Obligatorio si no está `cubierta`. |
| `notas` | texto | Comentario libre. |

### Por qué hay dos campos: `gramatical` y `cubierta`

| `gramatical` | `cubierta` | Ejemplo | Para qué sirve |
| --- | --- | --- | --- |
| sí | sí | *el gato come* | Debe aceptarse. |
| no | no | *el gatos come* | Debe rechazarse (concordancia). |
| sí | no | *come el gato* | Español correcto que la gramática no cubre. |

El tercer caso es el que permite responder dos preguntas del proyecto:

- **P1:** ¿qué analizan bien spaCy y Transformers que la CFG no puede?
- **P5:** ¿el LLM respeta las reglas o se desvía hacia su conocimiento del español? Si
  acepta *come el gato*, está siguiendo su conocimiento y no las reglas.

`gramatical = false` y `cubierta = true` no está permitido: la gramática no debería
aceptar español incorrecto.

### Árboles

Notación entre paréntesis, la misma de NLTK y del Penn Treebank:

```
(O (SN (DET el) (SUST gato)) (SV (V come)))
```

- Las etiquetas son las de [gramatica_es.md](gramatica_es.md) y deben coincidir exactamente.
- Las palabras se comparan sin distinguir mayúsculas (*El* = *el*).
- Los espacios y saltos de línea no importan.

## Resultados: `results/<sistema>.jsonl`

`<sistema>` es `parser`, `spacy`, `transformers`, `llm_zero_shot` o `llm_few_shot`.

```json
{"id": "S003", "sistema": "parser", "aceptada": false,
 "arbol": "(O (SN (DET el) (SUST gatos)) (SV (V come)))",
 "categorias": ["DET", "SUST", "V"],
 "tipo_error": "concordancia",
 "detalle": "Palabra 1 ('el'): ...", "extra": {}}
```

| Campo | Tipo | Significado |
| --- | --- | --- |
| `id` | texto | El `id` de la oración en el set de prueba. |
| `sistema` | texto | Quién produjo el resultado. |
| `aceptada` | booleano | Decisión del sistema. |
| `arbol` | texto o `null` | Árbol en nuestra notación, si el sistema lo produce (parser y LLM). El parser lo guarda aunque falle la concordancia. |
| `categorias` | lista o `null` | Una categoría por palabra, con nuestras etiquetas. Es lo que permite comparar con spaCy y Transformers, que no producen nuestros árboles. |
| `tipo_error` | `lexico` \| `sintactico` \| `concordancia` \| `otro` \| `null` | Por qué se rechazó. |
| `detalle` | texto | Mensaje de error, explicación del LLM, etc. |
| `extra` | objeto | Datos propios de cada sistema (análisis completo de spaCy, respuesta cruda del LLM…). |

<!-- TODO(P1 y P4): confirmar el formato. Si cambia, actualizar evaluation/formats.py
     y data/test_set.jsonl a la vez (las pruebas avisan si no coinciden). -->
