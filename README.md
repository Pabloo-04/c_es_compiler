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
$ python -m spanish.pipeline "Él mató un elefante muy gris ayer." --arbol
S
  NP
    NPbase
      Prn Él
  VP
    Verb mató
    NP
      NPbase
        Det un
        Nom
          Noun elefante
          AdjP
            Intens muy
            Adj gris
    Adv ayer

Sujeto: él · Verbo: mató · Objeto: elefante
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
python -m spanish.pipeline "Ella come una manzana."                    # acepta o rechaza
python -m spanish.pipeline "Ella come una manzana." --tokens --arbol    # palabras con rasgos y árbol
python -m spanish.pipeline "Ella come una manzana." --png results/figures/ella.png
python -m spanish.pipeline --archivo oraciones.txt               # una oración por línea
```

Una oración pasa por tres etapas. Si una falla, las siguientes no se ejecutan:

1. **Lexer:** separa las palabras y busca sus rasgos en el léxico (`data/lexicon.json`).
2. **Parser:** construye el árbol con la gramática (`spanish/grammar.py`).
3. **Concordancia:** verifica género, número y persona sobre el árbol.

Los errores indican la palabra y la causa:

```
[error de concordancia] Palabra 3 ('come'): el verbo 'come' (singular) no concuerda con el sujeto 'perros' (plural)
RECHAZADA
```

## Reproducir los experimentos

Todos los sistemas leen el mismo conjunto de prueba (`data/test_set.csv`) y escriben sus
resultados en el mismo formato en `results/` (ver [docs/gramatica_es.md (Parte 2)](docs/gramatica_es.md#parte-2-formato-de-salida)).

| Paso | Comando | Resultado |
| --- | --- | --- |
| 1. Nuestro parser | `python -m evaluation.run_parser` | `results/parser.jsonl` |
| 2. spaCy y Transformers | `jupyter lab notebooks/nlp_comparison.ipynb` | `results/spacy.jsonl`, `results/transformers.jsonl` |
| 3. LLM (zero-shot y few-shot) | `jupyter lab notebooks/llm_experiment.ipynb` | `results/llm_zero.jsonl`, `results/llm_few.jsonl` |
| 4. Métricas | `python -m evaluation.metrics` | tablas y `results/figures/` |

**Experimento con el LLM.** El proveedor se elige en la primera celda de configuración del
notebook (`PROVIDER`). La clave de API va en un archivo `.env` en la raíz del repositorio,
que no se sube a Git:

```
ANTHROPIC_API_KEY=...
```

Con `PROVIDER = "manual"` no hace falta clave: el notebook muestra cada prompt y se pega la
respuesta de cualquier chat. Todos los prompts y respuestas quedan en
`results/logs/llm.jsonl`. Si una oración ya está en el log, se reutiliza la respuesta en lugar de volver a llamar a la API.

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
| `test_agreement.py` | Concordancia Det/Pos–Noun–Adj y sujeto–verbo |
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
│   ├── reports.py              # matrices de confusión y reportes de clasificación
│   ├── hf_tagger.py            # etiquetado palabra por palabra con modelos de HuggingFace
│   ├── acceptability.py        # gramaticalidad con BETO (pseudo-log-verosimilitud y umbral)
│   ├── hf_loading.py           # descarga solo los archivos necesarios de cada modelo
│   ├── llm_client.py           # cliente intercambiable del LLM y registro de llamadas
│   └── prompts.py              # prompts zero-shot y few-shot
├── notebooks/
│   ├── nlp_comparison.ipynb    # spaCy y Transformers
│   └── llm_experiment.ipynb    # experimento con el LLM
├── data/
│   ├── lexicon.json            # léxico con rasgos
│   ├── calibration_acceptability.csv  # pares mínimos para calibrar el umbral de BETO
│   └── test_set.csv            # conjunto de prueba
├── results/                    # salidas de cada sistema, logs, figuras y reportes (reports/)
├── tests/
├── docs/
│   ├── gramatica_es.md         # gramática y formato de salida (acordados por el equipo)
│   └── informe/                # informe en LaTeX
└── fase1/                      # Fase 1 completa
```

## Documentación

- [Gramática y formato de salida](docs/gramatica_es.md): producciones, léxico, concordancia, ambigüedades, formato del conjunto de prueba y de los resultados, y cálculo de las métricas.
- [Informe](docs/informe/informe.tex): `cd docs/informe && latexmk -pdf informe.tex`.
