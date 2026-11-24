# Compilador Fase 2: análisis sintáctico del español con una gramática libre de contexto

**Integrantes:**

* Pablo Vides 00080323
* Gabriela Valiente 00010122
* Valeria Ortiz 00206022
* Paola Pérez Pérez 00117222
* Alejandro Melgar 00026222

Parser descendente recursivo para un fragmento del español, descrito por una gramática
libre de contexto con rasgos de concordancia. El proyecto compara este enfoque basado en
reglas con herramientas de NLP (spaCy y un modelo de HuggingFace Transformers) y con un
LLM al que se le dan las reglas de producción.

```
$ python -m spanish.pipeline "el perro negro comió la comida" --arbol
O
  SN
    DET el
    SUST perro
    SA
      ADJ negro
  SV
    V comió
    SN
      DET la
      SUST comida
ACEPTADA
```

La **Fase 1** (lexer y analizador semántico de un lenguaje estilo C) está en
[fase1/](fase1/README.md) y en el tag `fase-1` de Git.

## Requisitos e instalación

- Python 3.10 o superior.
- Para las imágenes de árboles: el programa Graphviz (`brew install graphviz` en macOS,
  `sudo apt install graphviz` en Linux).

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Para los experimentos (notebooks), además:

```bash
pip install -r requirements-experiments.txt
python -m spacy download es_core_news_sm
```

## Uso

```bash
python -m spanish.pipeline "el gato come"                        # acepta o rechaza
python -m spanish.pipeline "el gato come" --tokens --arbol       # palabras con rasgos y árbol
python -m spanish.pipeline "el gato come" --png results/figures/gato.png
python -m spanish.pipeline --archivo oraciones.txt               # una oración por línea
```

Una oración pasa por tres etapas. Si una falla, las siguientes no se ejecutan:

1. **Lexer:** separa las palabras y busca sus rasgos en el léxico (`data/lexicon.json`).
2. **Parser:** construye el árbol con la gramática (`spanish/grammar.py`).
3. **Concordancia:** verifica género, número y persona sobre el árbol.

Los errores indican la palabra y la causa:

```
[error de concordancia] Palabra 3 ('corre'): el sujeto 'los niños' (plural) no concuerda con el verbo 'corre' (singular)
RECHAZADA
```

## Reproducir los experimentos

Todos los sistemas leen el mismo set de prueba (`data/test_set.jsonl`) y escriben sus
resultados en el mismo formato en `results/` (ver [docs/formato_salida.md](docs/formato_salida.md)).

| Paso | Comando | Resultado |
| --- | --- | --- |
| 1. Nuestro parser | `python -m evaluation.run_parser` | `results/parser.jsonl` |
| 2. spaCy y Transformers | `jupyter lab notebooks/nlp_comparison.ipynb` | `results/spacy.jsonl`, `results/transformers.jsonl` |
| 3. LLM (zero-shot y few-shot) | `jupyter lab notebooks/llm_experiment.ipynb` | `results/llm_zero_shot.jsonl`, `results/llm_few_shot.jsonl` |
| 4. Métricas | `python -m evaluation.metrics` | tablas y `results/figures/` |

**Experimento con el LLM.** El proveedor se elige en la primera celda de configuración del
notebook (`PROVIDER`). La clave de API va en un archivo `.env` en la raíz del repositorio,
que no se sube a Git:

```
ANTHROPIC_API_KEY=...
```

Con `PROVIDER = "manual"` no hace falta clave: el notebook muestra cada prompt y se pega la
respuesta de cualquier chat. Todos los prompts y respuestas quedan en
`results/logs/llm_log.jsonl`.

## Pruebas

```bash
pytest
```

| Archivo | Qué prueba |
| --- | --- |
| `test_contracts.py` | Palabras, árboles (formato entre paréntesis) y mensajes de error |
| `test_grammar_and_data.py` | Que la gramática esté bien formada y que el léxico y el set de prueba sean coherentes con ella |
| `test_formats_and_prompts.py` | El formato de resultados y los prompts del LLM |
| `test_lexer.py` | Palabras, posiciones, tildes y palabras desconocidas |
| `test_parser.py` | Árboles de oraciones válidas y rechazo de las que están fuera de la gramática |
| `test_agreement.py` | Concordancia DET–SUST–ADJ y sujeto–verbo |
| `test_pipeline_and_metrics.py` | El parser sobre todo el set de prueba y las métricas |

Las pruebas de la Fase 1 se corren desde su carpeta: `cd fase1 && pytest`.

## Estructura del proyecto

```
c_compiler/
├── spanish/                    # el analizador
│   ├── tokens.py               # palabras, categorías y rasgos
│   ├── lexicon.py              # carga del léxico
│   ├── lexer.py                # analizador léxico
│   ├── grammar.py              # la gramática como datos (producciones)
│   ├── parser.py               # parser descendente recursivo
│   ├── tree.py                 # árbol sintáctico y notación entre paréntesis
│   ├── agreement.py            # verificación de concordancia
│   ├── trees.py                # visualización (graphviz / nltk)
│   ├── errors.py               # errores con formato único
│   └── pipeline.py             # lexer → parser → concordancia → visualización
├── evaluation/
│   ├── formats.py              # formato del set de prueba y de los resultados
│   ├── run_parser.py           # corre el parser sobre el set de prueba
│   └── metrics.py              # precisión, cobertura, rechazo correcto, errores
├── experiments/
│   ├── tagsets.py              # etiquetas de spaCy/Transformers → nuestras categorías
│   ├── llm_client.py           # cliente intercambiable del LLM y registro de llamadas
│   └── prompts.py              # prompts zero-shot y few-shot
├── notebooks/
│   ├── nlp_comparison.ipynb    # spaCy y Transformers
│   └── llm_experiment.ipynb    # experimento con el LLM
├── data/
│   ├── lexicon.json            # léxico con rasgos
│   └── test_set.jsonl          # set de prueba
├── results/                    # salidas de cada sistema, logs y figuras
├── tests/
├── docs/
│   ├── gramatica_es.md         # la gramática, explicada
│   ├── formato_salida.md       # formato del set de prueba y de los resultados
│   └── informe/                # informe en LaTeX
└── fase1/                      # Fase 1 completa
```

## Documentación

- [Gramática](docs/gramatica_es.md): producciones, categorías, rasgos y ambigüedades.
- [Formato de datos](docs/formato_salida.md): set de prueba y resultados.
- [Informe](docs/informe/informe.tex): `cd docs/informe && latexmk -pdf informe.tex`.
