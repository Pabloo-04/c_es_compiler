# Organización de la Fase 2

Documento interno del equipo: no forma parte de la entrega. El README queda limpio para la
entrega final.

Para encontrar lo pendiente de cada persona:

```bash
grep -rn "TODO(P3" spanish evaluation experiments notebooks tests docs
```

## Lo primero: acordar los contratos (día 1)

Como `Token` en la Fase 1, estas piezas conectan a todos y ya están implementadas. Hay que
revisarlas juntos antes de empezar, y no cambiarlas sin avisar:

| Contrato | Archivo | Lo usan |
| --- | --- | --- |
| `Token`, `Reading`, `Features` | `spanish/tokens.py` | P2, P3, P4 |
| `Node` y el formato de árbol entre paréntesis | `spanish/tree.py` | P2, P3, P4, P5 |
| Errores y `tipo_error` | `spanish/errors.py` | P2, P3, P4 |
| Set de prueba y resultados (JSONL) | `evaluation/formats.py`, `docs/formato_salida.md` | P1, P2, P4, P5 |
| La gramática como datos | `spanish/grammar.py` | P1, P2, P5 |

Mientras el lexer no esté listo, P2 y P3 prueban con `tests/helpers.py`
(`tokens_from_lexicon("el gato come")`).

## Archivos por persona

| Persona | Código | Documentación e informe |
| --- | --- | --- |
| **P1** Gramática, NLP e informe | `spanish/grammar.py`, `experiments/tagsets.py`, `notebooks/nlp_comparison.ipynb` | `docs/gramatica_es.md`, `docs/formato_salida.md` (con P4); informe: `01_marco_teorico`, `02_gramatica`, `07_comparacion_nlp`, `10_conclusiones`, edición final |
| **P2** Parser e integración | `spanish/parser.py`, `spanish/pipeline.py`, `evaluation/run_parser.py` | informe: `03_parser` |
| **P3** Lexer, concordancia y árboles | `spanish/lexer.py`, `spanish/lexicon.py`, `data/lexicon.json`, `spanish/agreement.py`, `spanish/trees.py` | informe: `04_lexer_concordancia_arboles` |
| **P4** Set de prueba y métricas | `data/test_set.jsonl` (60+ oraciones), `evaluation/metrics.py`, gráficas en `results/figures/` | `docs/formato_salida.md` (con P1); informe: `05_set_de_prueba`, `06_resultados` |
| **P5** LLM y repositorio | `experiments/llm_client.py`, `experiments/prompts.py`, `notebooks/llm_experiment.ipynb`, `README.md`, pruebas en `tests/` | informe: `08_analisis_llm`, `09_comparacion_enfoques` |

Equivalencia con los nombres del documento de roles: `comparar_nlp.py` →
`notebooks/nlp_comparison.ipynb`, `experimento_llm.py` → `notebooks/llm_experiment.ipynb`,
`semantico.py` → `spanish/agreement.py`, `arboles.py` → `spanish/trees.py`,
`metricas.py` → `evaluation/metrics.py`.

## Flujo de los experimentos

```
data/test_set.jsonl (P4)
   │
   ├─ python -m evaluation.run_parser        (P2) ─► results/parser.jsonl
   ├─ notebooks/nlp_comparison.ipynb         (P1) ─► results/spacy.jsonl, results/transformers.jsonl
   ├─ notebooks/llm_experiment.ipynb         (P5) ─► results/llm_zero_shot.jsonl, results/llm_few_shot.jsonl
   │                                                  results/logs/llm_log.jsonl
   └─ python -m evaluation.metrics           (P4) ─► tablas y results/figures/
```

## Reglas de trabajo

- **Código en inglés, documentación y datos en español** (como en la Fase 1).
- Una rama por tarea y pull request a `develop`; correr `pytest` antes de cada merge.
- Las pruebas de contratos y datos (`test_contracts.py`, `test_grammar_and_data.py`,
  `test_formats_and_prompts.py`) deben pasar siempre. Las demás fallan con
  `NotImplementedError` hasta que cada parte esté lista.
- **Nunca** subir claves de API: van en `.env`, que está en `.gitignore`.
- Los notebooks se suben **sin salidas** (Kernel → Restart & Clear Output) para evitar
  conflictos de Git; los resultados quedan en `results/`.

## Presentación

| Parte | Quién |
| --- | --- |
| Teoría y gramática | P1 |
| Demo en vivo del parser (`python -m spanish.pipeline "..." --tokens --arbol`) | P2 |
| Concordancia y árboles | P3 |
| Set de prueba y métricas | P4 |
| Experimento con el LLM | P5 |
| Comparación con NLP y conclusiones | P1 |
