# Gramática y formato de salida – Fase 2

Este archivo reúne las dos cosas que todo el grupo necesita tener iguales:

- **Parte 1. Gramática:** las reglas del subconjunto del español que analiza el parser. La usan `spanish/parser.py`, `spanish/agreement.py`, el conjunto de prueba y el prompt del LLM. Su versión ejecutable está en `spanish/grammar.py`.
- **Parte 2. Formato de salida:** cómo se escribe el conjunto de prueba y cómo guarda sus resultados cada sistema. `evaluation/metrics.py` solo lee esos archivos. Su versión ejecutable está en `evaluation/formats.py`.

Si se cambia algo de este archivo, se avisa al grupo antes de hacer *push*.

## Contenido

- [Parte 1. Gramática](#parte-1-gramática)
- [Parte 2. Formato de salida](#parte-2-formato-de-salida)
- [Referencias](#referencias)

---

## Parte 1. Gramática

Esta es la gramática libre de contexto (CFG) del subconjunto del español que analiza el parser del proyecto. Se basa en la gramática de ejemplo de Luque [1] y agrega cinco reglas para cubrir lo que pide el enunciado: Sujeto-Verbo-Objeto, adjetivos, adverbios, frases preposicionales y dos tiempos verbales.

- La **sección 1.1** es la versión para el informe.
- La **sección 1.2** es la versión que se programa en `spanish/parser.py`.
- Si se cambia una regla, hay que actualizar las dos versiones y avisar al grupo, porque esta gramática también va en el prompt del LLM.

---

### 1.1 Gramática ampliada (versión del informe)

Las reglas marcadas con ★ son nuevas. Todas las demás vienen de Luque [1].

```
S      → NP VP                                (oraciones)
NP     → Prn | Det Nom | Pos Nom | NP PP      (sintagmas nominales)
Nom    → Noun | Noun AdjP                ★    (núcleo nominal con adjetivo)
AdjP   → Adj | Intens Adj                ★    (sintagma adjetival: "muy grande")
VP     → Verb NP | VP PP                      (sintagmas verbales)
       | Verb                            ★    (verbo intransitivo: "duerme")
       | VP Adv                          ★    (modificador adverbial)
PP     → Prep NP                              (sintagmas preposicionales)
```

**Cambio respecto a Luque:** `Det Noun` y `Pos Noun` pasan a ser `Det Nom` y `Pos Nom`, para que el adjetivo entre sin duplicar reglas.

#### Gramática original de Luque [1]

Se incluye como referencia para ver qué se agregó:

```
S    → NP VP
NP   → Prn | Det Noun | Pos Noun | NP PP
VP   → Verb NP | VP PP
PP   → Prep NP
Prn  → él | ...
Det  → un | ...
Noun → elefante | pijamas | ...
Verb → mató | ...
Prep → en | ...
Pos  → sus | ...
```

#### Cobertura de los requisitos del enunciado

| Requisito | Regla o recurso |
|---|---|
| Sujeto-Verbo-Objeto | `S → NP VP` y `VP → Verb NP` (de Luque) |
| Adjetivos | `Nom → Noun AdjP` y `AdjP → Adj` ★ |
| Adverbios | `VP → VP Adv` ★ y `AdjP → Intens Adj` ★ |
| Frases preposicionales | `NP → NP PP`, `VP → VP PP` y `PP → Prep NP` (de Luque) |
| Dos tiempos verbales | Presente y pretérito, en el léxico (rasgo `tiempo`) |
| Concordancia | Rasgos de género, número y persona, verificados en `spanish/agreement.py` |

---

### 1.2 Versión sin recursión por la izquierda (versión de `spanish/parser.py`)

`NP → NP PP`, `VP → VP PP` y `VP → VP Adv` son recursivas por la izquierda, y un parser descendente recursivo entraría en un ciclo infinito con ellas. Se transforman con la regla estándar:

```
A → A α | β      ⇒      A  → β A'
                        A' → α A' | ε
```

Resultado:

```
S       → NP VP
NP      → NPbase NP'
NPbase  → Prn | Det Nom | Pos Nom
NP'     → PP NP' | ε
Nom     → Noun AdjOpc
AdjOpc  → AdjP | ε
AdjP    → Adj | Intens Adj
VP      → Verb ObjOpc VP'
ObjOpc  → NP | ε
VP'     → PP VP' | Adv VP' | ε
PP      → Prep NP
```

#### Cómo se programa

- Cada no terminal es un método de `Parser`: `sentence()`, `noun_phrase()`, `verb_phrase()`, etc. (el código va en inglés).
- Cada regla `X' → ... X' | ε` es un ciclo `while` que se repite mientras el token actual pueda iniciar la regla.
- Cada regla con `| ε` (`AdjOpc`, `ObjOpc`) es un `if` que revisa si el token actual puede iniciar la parte opcional.

| No terminal | Puede empezar con (FIRST) |
|---|---|
| `NP`, `NPbase` | `Prn`, `Det`, `Pos` |
| `Nom` | `Noun` |
| `AdjP` | `Adj`, `Intens` |
| `VP` | `Verb` |
| `PP` | `Prep` |

---

### 1.3 Léxico

Los dos tiempos verbales se resuelven en el léxico, no con reglas. Cada palabra lleva su categoría y sus rasgos, que usa `spanish/agreement.py` para verificar la concordancia. El léxico está en `data/lexicon.json`.

```
Prn    → él | ella | ellos
Det    → un | una | el | la | los | las
Pos    → sus | su | mi
Noun   → elefante | pijamas | niña | perro | perros | manzana
Adj    → grande | grandes | gris | grises | pequeña | rojos
Intens → muy | bastante
Adv    → ayer | hoy | rápidamente
Prep   → en | con | de
Verb   → mata | come | duerme | matan        (presente)
       | mató | comió | durmió | mataron     (pretérito)
```

Este vocabulario es el mínimo; cada quien puede agregar palabras al construir el conjunto de prueba, siempre que respeten las categorías.

#### Formato de los rasgos

```python
LEXICO = {
    "el":       {"cat": "Det",  "gen": "m", "num": "sg"},
    "niña":     {"cat": "Noun", "gen": "f", "num": "sg"},
    "rojos":    {"cat": "Adj",  "gen": "m", "num": "pl"},
    "ella":     {"cat": "Prn",  "gen": "f", "num": "sg", "pers": 3},
    "mató":     {"cat": "Verb", "tiempo": "pret", "pers": 3, "num": "sg"},
    "comen":    {"cat": "Verb", "tiempo": "pres", "pers": 3, "num": "pl"},
    "muy":      {"cat": "Intens"},
    "ayer":     {"cat": "Adv"},
    "en":       {"cat": "Prep"},
}
```

| Rasgo | Valores | Categorías |
|---|---|---|
| `gen` | `m`, `f` | Det, Pos, Noun, Adj, Prn |
| `num` | `sg`, `pl` | Det, Pos, Noun, Adj, Prn, Verb |
| `pers` | `1`, `2`, `3` | Prn, Verb (los sustantivos son 3.ª persona) |
| `tiempo` | `pres`, `pret` | Verb |

#### Reglas de concordancia (en `spanish/agreement.py`, no en la gramática)

1. **Dentro del NP:** `Det`/`Pos`, `Noun` y `Adj` deben coincidir en género y número.
   `los perros rojos` ✔ · `la elefante` ✘ · `los perro` ✘
2. **Sujeto-verbo:** el núcleo del NP sujeto y el verbo deben coincidir en número y persona.
   `los perros comen` ✔ · `los perros come` ✘

Los posesivos no marcan género (`su`, `sus`), así que solo se verifica el número. Los adjetivos invariables (`grande`, `gris`) tampoco llevan `gen`: un rasgo ausente concuerda con cualquier valor.

---

### 1.4 Decisiones de diseño

#### `Intens` y `Adv` son categorías distintas

Si "muy" fuera `Adv`, en *"comió la manzana muy rápidamente"* el parser no sabría, al ver un adverbio, si sigue un adjetivo (`AdjP`) o un modificador del verbo (`VP'`). Formalmente, FIRST(`AdjOpc`) y FOLLOW(`AdjOpc`) compartirían `Adv` y la gramática no sería LL(1) en ese punto. Con categorías separadas el conflicto desaparece.

#### La concordancia no se escribe en la gramática

Para escribirla en la CFG habría que duplicar `NP`, `Nom`, `AdjP`, `Det`, `Noun` y `Adj` por cada combinación de género y número (4 combinaciones), y además separar los verbos por persona y número. El número de reglas crecería de forma explosiva. Por eso la gramática acepta *"la elefante grises duerme"* y el analizador semántico la rechaza, igual que en la Fase 1 la regla de "declarar antes de usar" se verificaba con la tabla de símbolos.

#### Conflicto que no se puede eliminar: la ambigüedad de las PP

Es el ejemplo del propio Luque: *"Él mató un elefante en sus pijamas"*. Al llegar a "en", el parser tiene dos opciones:

- seguir en `NP'`: el elefante estaba en sus pijamas;
- cerrar el NP y pasar a `VP'`: él mató al elefante estando en pijamas.

`Prep` está en FIRST(`NP'`) y también en FOLLOW(`NP'`), así que **la gramática no es LL(1)**, y ninguna transformación lo arregla porque la ambigüedad es real.

**Decisión:** el parser pega la PP al sustantivo más cercano (sigue en `NP'` mientras vea una `Prep`). Se documenta como limitación en el informe. Para mostrar los dos árboles se puede cargar la gramática de la sección 1.1 en `nltk.ChartParser`, que devuelve todos los análisis posibles.

---

### 1.5 Oraciones de ejemplo

| Oración | ¿Acepta la CFG? | ¿Acepta el semántico? | Qué pone a prueba |
|---|---|---|---|
| Ella come una manzana. | Sí | Sí | SVO básico, presente |
| Los perros grandes durmieron. | Sí | Sí | Adjetivo, verbo intransitivo, pretérito |
| Él mató un elefante muy gris ayer. | Sí | Sí | Intensificador y adverbio |
| Mi niña comió la manzana con su perro. | Sí | Sí | PP con posesivo |
| Él mató un elefante en sus pijamas. | Sí (2 árboles) | Sí | Ambigüedad estructural |
| La elefante grises duerme. | Sí | **No** | Concordancia dentro del NP |
| Los perros come. | Sí | **No** | Concordancia sujeto-verbo |
| Come la manzana. | **No** | – | Sujeto omitido (el español lo permite) |
| La manzana roja que comió ella. | **No** | – | Subordinada (fuera de la gramática) |

Las dos últimas son correctas en español pero la gramática no las genera. Sirven para el nivel 3 del conjunto de prueba y para el análisis de fallas.

---

### 1.6 Opcional: tercer tiempo verbal

Si se quiere el pretérito perfecto compuesto (*"ha comido una manzana"*):

```
VP     → Aux Part ObjOpc VP'
Aux    → ha | han
Part   → matado | comido | dormido
```

`Aux` no choca con `Verb` porque son categorías distintas, así que la gramática sigue siendo LL(1) en ese punto.

---

## Parte 2. Formato de salida

Este documento fija cómo se escribe el conjunto de prueba y cómo guarda sus resultados cada sistema (parser propio, spaCy, Transformers y LLM). `evaluation/metrics.py` solo lee estos archivos, así que **todos deben usar exactamente estos nombres de campos y valores**.

Las categorías gramaticales son las de la [Parte 1](#parte-1-gramática).

---

### 2.1 Archivos

```
data/
  test_set.csv            ← conjunto de prueba con la salida esperada (Persona 4)
  lexicon.json            ← léxico con rasgos (Persona 3)
  calibration_acceptability.csv ← pares mínimos para calibrar el umbral de BETO (Persona 1; fuera del conjunto de prueba)
results/
  parser.jsonl            ← parser propio (Persona 2)
  spacy.jsonl             ← spaCy (Persona 1)
  transformers.jsonl      ← HuggingFace Transformers (Persona 1)
  llm_zero.jsonl          ← LLM, solo reglas (Persona 5)
  llm_few.jsonl           ← LLM, reglas y ejemplos (Persona 5)
  metrics.csv             ← métricas calculadas (Persona 4)
  logs/
    llm.jsonl             ← prompts y respuestas completas del LLM (Persona 5)
```

Las carpetas van en inglés, como el código; los nombres de las columnas y de los campos siguen en español.

Todos los archivos en **UTF-8**.

---

### 2.2 Categorías

Todos los sistemas etiquetan con este conjunto cerrado de categorías:

| Categoría | Significado | Ejemplos |
|---|---|---|
| `Prn` | Pronombre | él, ella, ellos |
| `Det` | Determinante | el, la, un, los |
| `Pos` | Posesivo | su, sus, mi |
| `Noun` | Sustantivo | elefante, niña |
| `Adj` | Adjetivo | grande, rojos |
| `Intens` | Intensificador | muy, bastante |
| `Adv` | Adverbio | ayer, rápidamente |
| `Verb` | Verbo | come, mató |
| `Prep` | Preposición | en, con, de |
| `X` | Cualquier otra palabra (fuera de la gramática) | que, y, no |

Si se agregan `Aux` y `Part` (tercer tiempo verbal opcional), se suman a esta tabla y se avisa al grupo.

Una palabra que no está en el léxico se etiqueta `X`. Como `X` no aparece en ninguna regla, la oración no se puede derivar y el parser la rechaza con `tipo_error = sintactico` (fenómeno `fuera_lexico`). Por eso no hace falta un tipo de error léxico.

---

### 2.3 Conjunto de prueba: `data/test_set.csv`

Una fila por oración. Lo construye la Persona 4.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | entero | Identificador único (1, 2, 3, …). Nunca se reutiliza. |
| `nivel` | 1, 2 o 3 | 1 = simple, 2 = intermedia, 3 = compleja. |
| `oracion` | texto | La oración, con mayúscula inicial y punto final. |
| `en_gramatica` | `si` / `no` | ¿Debe aceptarla el sistema completo (CFG + semántico)? Es la salida esperada del parser y del LLM. |
| `espanol_valido` | `si` / `no` | ¿Es correcta en español? Independiente de nuestra gramática. |
| `tipo_error` | `ninguno` / `sintactico` / `concordancia` | Por qué la rechaza nuestro sistema. `ninguno` si `en_gramatica = si`. |
| `fenomeno` | texto | Qué pone a prueba (lista abajo). |
| `etiquetas` | texto | Cada palabra con su categoría: `palabra/Cat`, separadas por un espacio. |
| `sujeto` | texto | Núcleo del sujeto (una palabra). Vacío si no hay sujeto explícito. |
| `verbo` | texto | Verbo principal (una palabra). |
| `objeto` | texto | Núcleo del objeto directo. Vacío si no hay. |

#### ¿Por qué dos columnas de gramaticalidad?

Porque no miden lo mismo, y la diferencia es uno de los hallazgos del proyecto:

| Oración | `en_gramatica` | `espanol_valido` | Qué muestra |
|---|---|---|---|
| Ella come una manzana. | si | si | Caso normal |
| La elefante grises duerme. | no | no | Error real, detectado por el semántico |
| Come la manzana. | no | si | Español correcto que la CFG no genera |

Con `en_gramatica` se mide si el parser y el LLM **siguen las reglas**. Con `espanol_valido` se mide si el LLM **se desvía hacia su conocimiento del español** (pregunta (a) del enunciado).

#### Valores de `fenomeno`

`svo`, `intransitivo`, `adjetivo`, `adverbio`, `intensificador`, `pp`, `posesivo`, `preterito`, `ambiguedad`, `concordancia_np`, `concordancia_sv`, `sujeto_omitido`, `subordinada`, `coordinacion`, `orden_libre`, `fuera_lexico`.

Si hay varios, se separan con `;` (por ejemplo `adjetivo;preterito`). Si hace falta uno nuevo, se agrega a esta lista.

#### Reglas para escribir las oraciones

1. **Sin contracciones** (`al`, `del`): spaCy las divide en dos palabras y los tokens dejarían de coincidir. Escribir `a el`, `de el` tampoco sirve; mejor elegir otra oración.
2. **Solo un punto final** como signo de puntuación; sin comas, comillas ni signos de interrogación.
3. **Las etiquetas no incluyen el punto** y deben tener el mismo número de palabras que la oración.
4. **Las palabras en `etiquetas` van en minúsculas**; `oracion` conserva la mayúscula inicial.
5. En oraciones con `en_gramatica = no`, las etiquetas siguen siendo las **correctas en español** (lo que debería decir un buen etiquetador), aunque nuestra gramática no las acepte.

#### Ejemplo

```csv
id,nivel,oracion,en_gramatica,espanol_valido,tipo_error,fenomeno,etiquetas,sujeto,verbo,objeto
1,1,Ella come una manzana.,si,si,ninguno,svo,ella/Prn come/Verb una/Det manzana/Noun,ella,come,manzana
2,2,Los perros grandes durmieron.,si,si,ninguno,adjetivo;intransitivo;preterito,los/Det perros/Noun grandes/Adj durmieron/Verb,perros,durmieron,
3,2,Él mató un elefante muy gris ayer.,si,si,ninguno,intensificador;adverbio;preterito,él/Prn mató/Verb un/Det elefante/Noun muy/Intens gris/Adj ayer/Adv,él,mató,elefante
4,3,Él mató un elefante en sus pijamas.,si,si,ninguno,ambiguedad;pp,él/Prn mató/Verb un/Det elefante/Noun en/Prep sus/Pos pijamas/Noun,él,mató,elefante
5,2,La elefante grises duerme.,no,no,concordancia,concordancia_np,la/Det elefante/Noun grises/Adj duerme/Verb,elefante,duerme,
6,2,Los perros come.,no,no,concordancia,concordancia_sv,los/Det perros/Noun come/Verb,perros,come,
7,3,Come la manzana.,no,si,sintactico,sujeto_omitido,come/Verb la/Det manzana/Noun,,come,manzana
```

---

### 2.4 Resultados de cada sistema: `results/<sistema>.jsonl`

Una línea JSON por oración del conjunto, **en el mismo orden y con el mismo `id`**. Si un sistema falla con una oración, igual escribe la línea con `"error_ejecucion"`.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | entero | El `id` de `test_set.csv`. |
| `sistema` | texto | `parser`, `spacy`, `transformers`, `llm_zero` o `llm_few`. |
| `acepta` | `true` / `false` / `null` | ¿La oración es válida según el sistema? `null` si el sistema no decide (spaCy siempre analiza algo). Transformers decide con un modelo de lenguaje (sección 2.6 bis). |
| `tipo_error` | texto / `null` | `sintactico`, `concordancia` o `null` si acepta o no decide. |
| `etiquetas` | lista | `[["palabra", "Cat"], ...]`, en minúsculas y sin el punto. `null` si el sistema no etiqueta. |
| `sujeto` | texto / `null` | Núcleo del sujeto. `""` si detecta que no hay sujeto; `null` si el sistema no lo calcula. |
| `verbo` | texto / `null` | Verbo principal. |
| `objeto` | texto / `null` | Núcleo del objeto directo. `""` si no hay; `null` si el sistema no lo calcula. |
| `arbol` | texto / `null` | Árbol en notación de corchetes (ver abajo). |
| `num_arboles` | entero / `null` | Cuántos análisis encontró (útil para `ambiguedad`). |
| `tiempo_ms` | número | Tiempo de procesamiento de la oración, en milisegundos. |
| `error_ejecucion` | texto / `null` | Mensaje si el sistema se cayó con esta oración. |

#### Árbol

Notación de corchetes, compatible con `nltk.Tree.fromstring()`, con las categorías de la gramática:

```
(S (NP (NPbase (Prn ella))) (VP (Verb come) (NP (NPbase (Det una) (Nom (Noun manzana))))))
```

Las reglas con ε (`NP'`, `AdjOpc`, `ObjOpc`, `VP'`) **no aparecen** en el árbol cuando quedan vacías.

**Árbol aplanado:** cuando no están vacías **tampoco aparecen**; lo que contienen cuelga directamente del nodo padre. Así el árbol es el mismo para el parser y para el LLM:

```
(S (NP (NPbase (Prn él)))
   (VP (Verb mató)
       (NP (NPbase (Det un) (Nom (Noun elefante)))
           (PP (Prep en) (NP (NPbase (Pos sus) (Nom (Noun pijamas))))))))
```

Hijos permitidos de cada nodo (`TREE_SHAPES` en `spanish/grammar.py`):

| Nodo | Hijos |
|---|---|
| `S` | `NP VP` |
| `NP` | `NPbase`, seguido de cero o más `PP` |
| `NPbase` | `Prn` · `Det Nom` · `Pos Nom` |
| `Nom` | `Noun`, seguido de un `AdjP` opcional |
| `AdjP` | `Adj` · `Intens Adj` |
| `VP` | `Verb`, un `NP` opcional, y cero o más `PP` o `Adv` |
| `PP` | `Prep NP` |

Las palabras del árbol van en minúsculas, como en `etiquetas`.

#### Qué llena cada sistema

| Campo | Parser | spaCy | Transformers | LLM |
|---|---|---|---|---|
| `acepta` | ✔ | `null` | ✔ (BETO, umbral de PLL) | ✔ |
| `tipo_error` | ✔ | `null` | `null` (no sabe por qué) | ✔ |
| `etiquetas` | ✔ (si acepta o falla en el semántico) | ✔ | ✔ | ✔ |
| `sujeto`, `verbo`, `objeto` | ✔ | ✔ (dependencias) | `null` si el modelo solo hace POS | ✔ |
| `arbol` | ✔ | `null` | `null` | ✔ |

#### Ejemplos

Parser propio:

```json
{"id": 1, "sistema": "parser", "acepta": true, "tipo_error": null, "etiquetas": [["ella", "Prn"], ["come", "Verb"], ["una", "Det"], ["manzana", "Noun"]], "sujeto": "ella", "verbo": "come", "objeto": "manzana", "arbol": "(S (NP (NPbase (Prn ella))) (VP (Verb come) (NP (NPbase (Det una) (Nom (Noun manzana))))))", "num_arboles": 1, "tiempo_ms": 0.4, "error_ejecucion": null}
{"id": 5, "sistema": "parser", "acepta": false, "tipo_error": "concordancia", "etiquetas": [["la", "Det"], ["elefante", "Noun"], ["grises", "Adj"], ["duerme", "Verb"]], "sujeto": "elefante", "verbo": "duerme", "objeto": "", "arbol": null, "num_arboles": null, "tiempo_ms": 0.3, "error_ejecucion": null}
```

spaCy:

```json
{"id": 1, "sistema": "spacy", "acepta": null, "tipo_error": null, "etiquetas": [["ella", "Prn"], ["come", "Verb"], ["una", "Det"], ["manzana", "Noun"]], "sujeto": "ella", "verbo": "come", "objeto": "manzana", "arbol": null, "num_arboles": null, "tiempo_ms": 6.2, "error_ejecucion": null}
```

---

### 2.5 Conversión de spaCy y Transformers a nuestras categorías

Ambos devuelven etiquetas UPOS de Universal Dependencies. Esta es la tabla de conversión que deben usar los notebooks, para que nadie la invente por su cuenta:

| UPOS | Condición | Nuestra categoría |
|---|---|---|
| `PRON` | – | `Prn` |
| `DET` | con rasgo `Poss=Yes` | `Pos` |
| `DET` | resto | `Det` |
| `NOUN`, `PROPN` | – | `Noun` |
| `ADJ` | – | `Adj` |
| `ADV` | su núcleo (`head`) es un `ADJ` y va justo antes de él | `Intens` |
| `ADV` | resto | `Adv` |
| `VERB`, `AUX` | – | `Verb` |
| `ADP` | – | `Prep` |
| `PUNCT` | – | se descarta |
| cualquier otra | – | `X` |

Si el modelo de Transformers no da rasgos ni dependencias, `DET` se convierte en `Pos` solo si la palabra es `su`, `sus`, `mi`, `mis`, `tu`, `tus`, y `ADV` en `Intens` solo si es `muy`, `bastante`, `poco`, `tan`.

Sujeto, verbo y objeto desde las dependencias de spaCy:

- `verbo`: la palabra con relación `ROOT`.
- `sujeto`: la palabra con relación `nsubj` cuyo núcleo es el `ROOT`; `""` si no hay.
- `objeto`: la palabra con relación `obj` cuyo núcleo es el `ROOT`; `""` si no hay.

```python
CONVERSION = {"PRON": "Prn", "NOUN": "Noun", "PROPN": "Noun", "ADJ": "Adj",
              "VERB": "Verb", "AUX": "Verb", "ADP": "Prep"}

def categoria(token):
    if token.pos_ == "DET":
        return "Pos" if "Yes" in token.morph.get("Poss") else "Det"
    if token.pos_ == "ADV":
        antes_del_adj = token.head.pos_ == "ADJ" and token.i == token.head.i - 1
        return "Intens" if antes_del_adj else "Adv"
    return CONVERSION.get(token.pos_, "X")

def salida_spacy(id_, doc, tiempo_ms):
    tokens = [t for t in doc if t.pos_ != "PUNCT"]
    raiz = next((t for t in doc if t.dep_ == "ROOT"), None)
    def rol(dep):
        return next((t.text.lower() for t in doc if t.dep_ == dep and t.head == raiz), "")
    return {
        "id": id_, "sistema": "spacy", "acepta": None, "tipo_error": None,
        "etiquetas": [[t.text.lower(), categoria(t)] for t in tokens],
        "sujeto": rol("nsubj"), "verbo": raiz.text.lower() if raiz else "",
        "objeto": rol("obj"), "arbol": None, "num_arboles": None,
        "tiempo_ms": tiempo_ms, "error_ejecucion": None,
    }
```

---

### 2.6 bis Gramaticalidad con Transformers

Para que Transformers tenga un `acepta` real se usa un modelo de lenguaje con máscara en español, BETO
(`dccuchile/bert-base-spanish-wwm-cased`), sin entrenar nada (`experiments/acceptability.py`):

- **Puntuación:** pseudo-log-verosimilitud (PLL) promedio por fragmento, con la variante *word-l2r*
  (se enmascaran también los fragmentos siguientes de la misma palabra). Mayor = más aceptable.
- **Umbral:** el de mayor exactitud sobre `data/calibration_acceptability.csv` (pares mínimos que no
  están en el conjunto de prueba).
- **Decisión:** `acepta = puntuación >= umbral`. `tipo_error` queda en `null`: el modelo no sabe *por
  qué* una oración está mal.

En `results/transformers.jsonl`, `acepta` viene de BETO y `etiquetas` del etiquetador
(`wietsedv/xlm-roberta-base-ft-udpos28-es`). `tiempo_ms` suma los dos.

---

### 2.6 Salida del LLM

El prompt le pide al LLM que responda **solo** con este JSON, sin texto adicional:

```json
{"acepta": true, "tipo_error": null, "etiquetas": [["ella", "Prn"], ["come", "Verb"], ["una", "Det"], ["manzana", "Noun"]], "sujeto": "ella", "verbo": "come", "objeto": "manzana", "arbol": "(S (NP (NPbase (Prn ella))) (VP (Verb come) (NP (NPbase (Det una) (Nom (Noun manzana))))))"}
```

El notebook completa `id`, `sistema`, `num_arboles` (1 si hay árbol), `tiempo_ms` y `error_ejecucion`. Si la respuesta no es un JSON válido, la línea se escribe con `"acepta": null` y `"error_ejecucion": "respuesta_no_json"`, y cuenta como fallo del LLM.

#### Log: `results/logs/llm.jsonl`

Una línea por llamada a la API, aunque la respuesta sea inválida:

```json
{"id": 1, "sistema": "llm_zero", "modelo": "nombre-exacto-del-modelo", "temperature": 0, "prompt": "...", "respuesta_cruda": "...", "fecha": "2026-11-25T14:03:11-06:00"}
```

Este archivo es un entregable obligatorio. Antes de llamar a la API, el notebook revisa si ese `id` y `sistema` ya están en el log y, si lo están, reutiliza la respuesta.

---

### 2.7 Cómo se calculan las métricas (`evaluation/metrics.py`)

Hay tres comparaciones. Cada sistema participa en las que tienen datos (`null` se excluye).

#### a) Aceptación (parser, Transformers y LLM)

Se compara `acepta` con `en_gramatica`. La clase positiva es "acepta".

| | Esperado `si` | Esperado `no` |
|---|---|---|
| **Acepta** | VP | FP (falso positivo) |
| **Rechaza** | FN (falso negativo) | VN |

- Precisión = VP / (VP + FP)
- Cobertura (recall) = VP / (VP + FN)
- Tasa de rechazo correcto = VN / (VN + FP)

Para Transformers y el LLM también se calcula contra `espanol_valido`. Si coinciden más con `espanol_valido` que con `en_gramatica`, siguen su conocimiento general del español y no nuestras reglas. `tipo_error` no se compara para Transformers, porque siempre es `null`.

#### b) Etiquetado (todos los sistemas)

Se comparan las etiquetas palabra por palabra con `etiquetas` del conjunto.

- Exactitud = palabras con la categoría correcta / total de palabras.
- Precisión y cobertura **por categoría** (por ejemplo, qué tan bien detecta `Adj`).
- Error de etiquetado = palabra con categoría distinta a la esperada.

Si un sistema produce un número distinto de palabras que la oración, la oración completa cuenta como error de etiquetado y se reporta aparte.

#### c) Funciones sintácticas (todos menos Transformers si solo hace POS)

Se compara `sujeto`, `verbo` y `objeto` con el conjunto, por coincidencia exacta de la palabra. Se reporta el porcentaje de aciertos de cada uno.

#### Salida: `results/metrics.csv`

```csv
sistema,comparacion,nivel,metrica,valor
parser,aceptacion,todos,precision,0.95
parser,aceptacion,1,precision,1.00
spacy,etiquetado,todos,exactitud,0.91
llm_few,aceptacion_espanol,todos,precision,0.88
```

`nivel` es `1`, `2`, `3` o `todos`, para poder graficar por nivel de complejidad. Los valores del ejemplo son inventados.

---

## Referencias

[1] F. M. Luque, "El lenguaje natural como lenguaje formal", arXiv:1703.04417. Disponible en: https://arxiv.org/abs/1703.04417
