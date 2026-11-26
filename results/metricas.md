# Resultados de las métricas

Generado con `python -m evaluation.metrics`. Definiciones: `docs/gramatica_es.md`, sección 2.7.

## Composición del conjunto de prueba

| Nivel | Oraciones | En la gramática | Fuera de la gramática | Válidas fuera de la gramática | Error sintáctico | Error de concordancia | Con PP |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nivel 1 | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| Nivel 2 | 29 | 18 | 11 | 0 | 1 | 10 | 6 |
| Nivel 3 | 24 | 7 | 17 | 11 | 14 | 3 | 11 |
| Todos | 73 | 45 | 28 | 11 | 15 | 13 | 17 |

## Fenómenos por nivel (una oración puede tener varios)

| Fenómeno | Nivel 1 | Nivel 2 | Nivel 3 | Total |
| --- | --- | --- | --- | --- |
| svo | 14 | 7 | 1 | 22 |
| intransitivo | 6 | 9 | 0 | 15 |
| adjetivo | 0 | 10 | 4 | 14 |
| adverbio | 0 | 4 | 3 | 7 |
| intensificador | 0 | 4 | 2 | 6 |
| pp | 0 | 6 | 11 | 17 |
| posesivo | 3 | 6 | 3 | 12 |
| preterito | 7 | 8 | 7 | 22 |
| ambiguedad | 0 | 1 | 2 | 3 |
| concordancia np | 0 | 5 | 1 | 6 |
| concordancia sv | 0 | 5 | 3 | 8 |
| sujeto omitido | 0 | 0 | 2 | 2 |
| subordinada | 0 | 0 | 2 | 2 |
| coordinacion | 0 | 0 | 3 | 3 |
| orden libre | 0 | 0 | 3 | 3 |
| fuera lexico | 0 | 0 | 3 | 3 |

## Aceptación contra en_gramatica (las reglas)

| Sistema | Precisión | Cobertura | Rechazo correcto | Exactitud | F1 | Tipo de error |
| --- | --- | --- | --- | --- | --- | --- |
| Parser propio | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

## Aceptación contra espanol_valido (el español)

| Sistema | Precisión | Cobertura | Rechazo correcto | Exactitud | F1 |
| --- | --- | --- | --- | --- | --- |
| Parser propio | 1.00 | 0.80 | 1.00 | 0.85 | 0.89 |

## Exactitud de la aceptación por nivel (contra en_gramatica)

| Sistema | Nivel 1 | Nivel 2 | Nivel 3 | Todos |
| --- | --- | --- | --- | --- |
| Parser propio | 1.00 | 1.00 | 1.00 | 1.00 |

## Tipo de error esperado frente a la respuesta (oraciones fuera de la gramática)

| Sistema | Esperado | acepta | sintactico | concordancia | sin tipo | sin decision |
| --- | --- | --- | --- | --- | --- | --- |
| Parser propio | sintactico | 0 | 15 | 0 | 0 | 0 |
| Parser propio | concordancia | 0 | 0 | 13 | 0 | 0 |

## Etiquetado palabra por palabra

| Sistema | Etiquetas | Distinto largo |
| --- | --- | --- |
| Parser propio | 1.00 | 0 |

## Funciones sintácticas (coincidencia exacta)

| Sistema | Sujeto | Verbo | Objeto |
| --- | --- | --- | --- |
| Parser propio | 1.00 | 1.00 | 1.00 |

## Exactitud del etiquetado por nivel

| Sistema | Nivel 1 | Nivel 2 | Nivel 3 | Todos |
| --- | --- | --- | --- | --- |
| Parser propio | 1.00 | 1.00 | 1.00 | 1.00 |

## Cobertura (recall) del etiquetado por categoría

| Categoría | Parser propio |
| --- | --- |
| Prn | 1.00 |
| Det | 1.00 |
| Pos | 1.00 |
| Noun | 1.00 |
| Adj | 1.00 |
| Intens | 1.00 |
| Adv | 1.00 |
| Verb | 1.00 |
| Prep | 1.00 |

## Unión de la PP

| Sistema | Exactitud | Ambiguas detectadas |
| --- | --- | --- |
| Parser propio | 0.59 | 0.00 |

## Unión de la PP: esperado frente a predicho

| Sistema | Esperado | sustantivo | verbo | ambigua | sin respuesta |
| --- | --- | --- | --- | --- | --- |
| Parser propio | sustantivo | 6 | 0 | 0 | 0 |
| Parser propio | verbo | 4 | 4 | 0 | 1 |
| Parser propio | ambigua | 2 | 0 | 0 | 0 |

## Costo

| Sistema | Tiempo medio (ms) | Errores de ejecución |
| --- | --- | --- |
| Parser propio | 0.03 | 0 |
