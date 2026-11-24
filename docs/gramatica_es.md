# Gramática libre de contexto del español (fragmento)

**Responsable:** Persona 1

La versión ejecutable de esta gramática es `PRODUCTIONS` en
[spanish/grammar.py](../spanish/grammar.py). Este documento la explica y la justifica.
Si cambia una, hay que cambiar la otra; `tests/test_grammar_and_data.py` verifica que
los árboles del set de prueba se puedan derivar con ella.

Para imprimirla tal como la ve el LLM:

```bash
python -c "from spanish.grammar import as_bnf; print(as_bnf())"
```

## 1. Alcance

El enunciado pide:

| Requisito | Cómo se cubre |
| --- | --- |
| Oraciones Sujeto-Verbo-Objeto | `O → SN SV`, `SV → V SN` |
| Adjetivos | `SN → DET SUST SA`, `SA → ADJ` |
| Adverbios | `SA → ADV ADJ`, `SV → V SAdv` |
| Frases preposicionales | `SP → PREP SN`, `SV → V SP`, `SV → V SN SP` |
| Dos tiempos verbales | Rasgo `tiempo` del verbo (presente, pretérito); no cambia las producciones |
| Concordancia básica | Rasgos `genero`, `numero` y `persona`, verificados por `agreement.py` |

<!-- TODO(P1): confirmar los dos tiempos verbales y si entran el pretérito
     imperfecto, los verbos auxiliares o los tiempos compuestos. -->

## 2. Categorías

### Terminales (categorías léxicas)

| Símbolo | Categoría | Ejemplos | Rasgos |
| --- | --- | --- | --- |
| `DET` | determinante | el, la, los, un, una | género, número |
| `SUST` | sustantivo | gato, casa | género, número (3.ª persona) |
| `NPROP` | nombre propio | Ana | género, número (3.ª persona, singular) |
| `PRON` | pronombre personal sujeto | ella, nosotros | género, número, persona |
| `ADJ` | adjetivo | negro, pequeña, grande | género (puede faltar), número |
| `V` | verbo | come, comió | número, persona, tiempo |
| `ADV` | adverbio | rápidamente, muy | — |
| `PREP` | preposición | en, con, bajo | — |

### No terminales (sintagmas)

| Símbolo | Nombre |
| --- | --- |
| `O` | oración (símbolo inicial) |
| `SN` | sintagma nominal |
| `SV` | sintagma verbal |
| `SA` | sintagma adjetival |
| `SAdv` | sintagma adverbial |
| `SP` | sintagma preposicional |

## 3. Producciones

Punto de partida (el mismo de `spanish/grammar.py`):

```bnf
O    ::= SN SV
SN   ::= DET SUST | DET SUST SA | NPROP | PRON
SA   ::= ADJ | ADV ADJ
SV   ::= V | V SN | V SP | V SN SP | V SAdv | V SN SAdv
SAdv ::= ADV
SP   ::= PREP SN
```

<!-- TODO(P1): revisar y completar. Preguntas abiertas:
     - ¿SN → DET SA SUST ("la pequeña niña")?
     - ¿SN → DET SUST SP ("el libro de Ana")? Crea ambigüedad con SV → V SN SP.
     - ¿Adverbio antes del verbo ("Ana siempre come")?
     - ¿Conjunciones ("el gato y el perro")? -->

## 4. Rasgos y concordancia

La concordancia no se escribe en las producciones: se verifica después, sobre el árbol
(`spanish/agreement.py`). Es la misma división que en la Fase 1 entre la gramática y la
tabla de símbolos.

| Regla | Dónde | Ejemplo correcto | Ejemplo incorrecto |
| --- | --- | --- | --- |
| DET y SUST concuerdan en género y número | dentro de cada `SN` | *el gato* | \**la gato*, \**el gatos* |
| ADJ y SUST concuerdan en género y número | dentro de cada `SN` | *la niña pequeña* | \**la niña negro* |
| Sujeto y verbo concuerdan en número y persona | `O → SN SV` | *los niños corren* | \**los niños corre* |

Un rasgo ausente se considera compatible con cualquier valor: *grande* no tiene género, así
que concuerda con *la casa* y con *el gato*.

**Por qué no en la CFG.** Una CFG puede expresar estos rasgos multiplicando las categorías
(`SN_masc_sg`, `SN_fem_pl`…), pero el número de reglas crece con cada rasgo. Con 2 géneros,
2 números y 3 personas, cada regla se repite hasta 12 veces.
<!-- TODO(P1): desarrollar el análisis formal de fallas (sección del informe):
     qué no puede describir esta gramática y por qué. -->

## 5. Ambigüedad

| Fuente | Ejemplo | Cómo se resuelve |
| --- | --- | --- |
| Léxica (una palabra, varias categorías) | *bajo* = ADJ o PREP | El parser prueba las lecturas; la gramática descarta las que no encajan. |
| Estructural (dónde se une un SP) | *lee un libro en la casa* | Hoy solo `SV → V SN SP`. Si se agrega `SN → DET SUST SP`, hay dos árboles. |

<!-- TODO(P1): decidir la política ante oraciones con dos árboles (el parser
     devuelve el primero que encuentra; el set de prueba debe esperar ese). -->

## 6. Ejemplos

```
el gato come
(O (SN (DET el) (SUST gato)) (SV (V come)))

la niña pequeña lee un libro en la casa
(O (SN (DET la) (SUST niña) (SA (ADJ pequeña)))
   (SV (V lee) (SN (DET un) (SUST libro)) (SP (PREP en) (SN (DET la) (SUST casa)))))
```
