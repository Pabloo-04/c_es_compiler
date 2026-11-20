# Compilador Fase 1: lexer y analizador semántico

**Integrantes:**

* Pablo Vides 00080323
* Alejandro Melgar
* Gabriela

Lexer y analizador semántico en Python para un lenguaje propio estilo C con
palabras clave en español. Los programas fuente usan la extensión `.esp`.

```c
entero x = 1;
si (x > 0) {
    real x = 2.5;      // shadowing: otra x en un ámbito interno
    imprimir(x);
} sino {
    imprimir(0);
}
```

## Requisitos e instalación

- Python 3.10 o superior.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

```bash
python main.py examples/valid.esp                  # lexer + semántico
python main.py examples/valid.esp --tokens         # además muestra la tabla de tokens
python main.py examples/scopes.esp --simbolos      # además muestra la tabla de símbolos
python main.py examples/valid.esp --tokens --simbolos
python main.py examples/lexical_errors.esp --lexer-only
python main.py examples/semantic_errors.esp
```

Errores y advertencias se muestran ordenados por posición, con un único formato
(en rojo los errores y en amarillo las advertencias cuando la salida es una terminal):

```
=== Errores semánticos (2) ===
Línea 2, columna 12: no se puede asignar bool a entero
Línea 4, columna 8: variable 'y' ya declarada en este ámbito (línea 3)
```

`--simbolos` muestra todas las variables declaradas con su ámbito, tipo, posición y
si fueron inicializadas y usadas; los ámbitos internos aparecen indentados para que
se vea el shadowing.

Si hay errores léxicos no se corre el semántico. Mientras el semántico no esté
implementado, `main.py` lo avisa y muestra igual el resultado del lexer.

Código de salida: `0` sin errores (puede haber advertencias), `1` con errores y `2`
si no se pudo leer el archivo.

## Pruebas

```bash
pytest            # todas
pytest -v tests/test_lexer.py
```

> Al principio casi todas las pruebas fallan con `NotImplementedError`, y es lo
> esperado: describen el comportamiento que falta implementar. Cada uno sabe que
> terminó su parte cuando sus pruebas pasan.

## Estructura del proyecto

```
c_compiler/
├── main.py                    # CLI (listo)
├── compiler/
│   ├── tokens.py              # Token y TokenType: contrato compartido (listo)
│   ├── errors.py              # errores y advertencias: formato común (listo)
│   ├── lexer.py               # P2
│   ├── symbol_table.py        # P3
│   ├── statements.py          # P4: agrupar tokens en sentencias
│   ├── type_rules.py          # P4: reglas de tipos
│   └── semantic.py            # P3 + P4: orquesta el análisis
├── tests/
│   ├── helpers.py             # tokens_by_hand(): tokens sin depender del lexer
│   ├── test_errors.py
│   ├── test_lexer.py
│   ├── test_token_spec.py
│   ├── test_symbol_table.py
│   └── test_semantic.py
├── examples/                  # programas .esp para las demos
└── docs/
    ├── especificacion_tokens.md   # P1
    ├── gramatica.md               # gramática en BNF y EBNF
    ├── automata.md                # P1
    ├── reflexion.md               # P1
    └── guion_video.md             # P1
```

Para encontrar lo que falta: `grep -rn "TODO(P3)" .` (o el número de cada persona).

## Diseño

### Flujo

```
código fuente ──► lexer.tokenize() ──► list[Token] ──► semantic.analyze() ──► list[CompileError]
                        │                                   │
                        └─► errores léxicos                 ├─ statements.group()             (P4)
                                                            ├─ SymbolTable                    (P3)
                                                            └─ type_rules.expression_type()   (P4)
```

### Contrato `Token` (acordado el día 1)

```python
@dataclass(frozen=True)
class Token:
    type: TokenType   # INT, ID, REAL_LITERAL, EQUAL, LBRACE, EOF, ...
    lexeme: str       # texto exacto: "x", "3.14", "=="
    line: int         # desde 1
    column: int       # desde 1, primer carácter del lexema
```

El lexer siempre termina la lista con un token `EOF`. **No cambiar `tokens.py` sin avisar a todo el equipo.**

### Errores y advertencias

Las dos fases **acumulan** los diagnósticos en una lista y siguen analizando;
no se detienen en el primero. Todos se imprimen con un único formato:

```
Línea 7, columna 3: variable 'y' no declarada
```

| Clase (`compiler/errors.py`) | Uso |
| --- | --- |
| `LexicalError(line, column, message)` | Errores del lexer |
| `SemanticError(line, column, message)` | Errores del semántico |
| `CompileWarning(line, column, message)` | Advertencias: el programa sigue siendo válido |

`LexicalError` y `SemanticError` heredan de `CompileError`. `error.labeled()` agrega
el tipo adelante (`[error semántico] Línea 7, columna 3: ...`).

Advertencias previstas (TODO de P3 en `semantic.py`): variable sin usar, shadowing
y uso sin inicializar. Si hay errores léxicos, `main.py` no corre el semántico.

### Sentencias

No hay parser completo en esta fase. `statements.group()` produce una lista
**plana** de sentencias: `DECLARATION`, `ASSIGNMENT`, `IF`, `ELSE`, `WHILE`,
`PRINT`, `OPEN_BLOCK` (`{`) y `CLOSE_BLOCK` (`}`). El semántico la recorre en
orden: `{` abre un ámbito en la tabla de símbolos y `}` lo cierra.

### Tipos


| Operación                           | Resultado      |
| ------------------------------------ | -------------- |
| `entero + entero` (también `- * /`) | `entero`       |
| `entero + real`, `real + real`       | `real`         |
| `< > <= >=` entre números           | `bool`         |
| `== !=`                              | `bool`         |
| `&& ||` entre `bool`, `!bool`        | `bool`         |
| condición de`si` / `mientras`       | debe ser`bool` |

<!-- TODO(P4): confirmar la tabla y decidir si `real x = 5;` es válido. -->

## El lenguaje

### Tokens


| Token               | Expresión regular                                                                   |
| ------------------- | ------------------------------------------------------------------------------------ |
| Palabras reservadas | `entero`, `real`, `bool`, `si`, `sino`, `mientras`, `imprimir`, `verdadero`, `falso` |
| ID                  | `[a-zA-Z_][a-zA-Z0-9_]*` (después de descartar las palabras reservadas)             |
| NUM_ENTERO          | `[0-9]+`                                                                             |
| NUM_REAL            | `[0-9]+\.[0-9]+`                                                                     |
| Operadores          | `==`, `!=`, `<=`, `>=`, `&&`, `||`, `+`, `-`, `*`, `/`, `<`, `>`, `=`, `!`           |
| Delimitadores       | `(`, `)`, `{`, `}`, `;`, `,`                                                         |
| Comentarios         | `//.*` y `/\*(.|\n)*?\*/`                                                            |

La especificación formal y el autómata están en [docs/especificacion_tokens.md](docs/especificacion_tokens.md) y [docs/automata.md](docs/automata.md). La versión ejecutable de las expresiones regulares es `TOKEN_PATTERNS` en `compiler/tokens.py`, y `tests/test_token_spec.py` verifica que el lexer coincide con ella.

La gramática completa (léxica y sintáctica, en BNF y EBNF, con precedencia de operadores) está en [docs/gramatica.md](docs/gramatica.md).

### Sentencias

```
tipo ID ;              tipo ID = expr ;          ID = expr ;
si ( expr ) { ... }    si ( expr ) { ... } sino { ... }
mientras ( expr ) { ... }                        imprimir ( expr ) ;
```

No hay funciones en esta fase: los bloques de `si` y `mientras` bastan para demostrar los ámbitos.

## Reflexión

**¿Qué verificaciones del analizador semántico no puede expresar una gramática libre de
contexto, y por qué?**

### 1. Cada fase, un nivel de la jerarquía de Chomsky

| Fase | Tipo de lenguaje | Reconocedor | Qué necesita recordar |
| --- | --- | --- | --- |
| Lexer | Regular (tipo 3) | Autómata finito | Nada más que el estado actual (memoria finita) |
| Sintaxis | Libre de contexto (tipo 2) | Autómata de pila | Una pila: qué llaves y paréntesis siguen abiertos |
| Semántico | Más allá de libre de contexto | Tabla de símbolos | Todos los nombres declarados, con su tipo y su ámbito |

- **Los tokens son regulares.** Cada token se define con una expresión regular, y por el
  teorema de Kleene lo reconoce un autómata finito
  (ver [docs/latex/automata.pdf](docs/latex/automata.pdf)).
- **La sintaxis ya no es regular.** Los bloques anidados `{ { } }` tienen la forma
  { `{`ⁿ `}`ⁿ }, que exige contar sin límite. Un autómata finito no puede hacerlo; uno
  con una pila sí: apila cada `{` y desapila cada `}`. Eso es exactamente una gramática
  libre de contexto ([docs/gramatica.md](docs/gramatica.md)).
- **El semántico va un paso más allá.** Ya no basta con saber cuántas llaves hay
  abiertas: hay que recordar *qué nombres* se declararon. Una pila solo deja ver el
  elemento de arriba, y eso no alcanza para compararlos.

### 2. Lo que la CFG acepta y el semántico rechaza

Todas estas líneas de [examples/semantic_errors.esp](examples/semantic_errors.esp) son
**sintácticamente correctas**: se derivan de la gramática. Aun así, el programa es
inválido.

| Verificación | Ejemplo | Por qué la CFG no la expresa |
| --- | --- | --- |
| Declaración antes del uso | `z = 3;` sin `entero z;` antes | La regla `<asignacion> ::= ID "=" <expresion> ";"` acepta cualquier `ID`. Saber si `z` se declaró exige comparar este nombre con uno escrito antes, a distancia arbitraria. |
| Sin redeclaración en un ámbito | `entero y = 1;` … `entero y = 2;` | Hay que comparar cada nombre nuevo con *todos* los del mismo ámbito. |
| Ámbitos | `w = 2;` después de cerrar el bloque donde se declaró `w` | La CFG sabe que las llaves están balanceadas, pero no a qué declaración se refiere cada nombre. |
| Tipos en la asignación | `entero x = verdadero;` | Ver el matiz que sigue. |
| Condiciones `bool` | `si (y) { ... }` con `entero y` | El tipo de `y` está en su declaración, no en la condición. |

**Un matiz sobre los tipos.** Una CFG *sí* podría rechazar `entero x = verdadero;`.
Como hay solo tres tipos, se puede dividir `<expresion>` en `<expr_entero>`,
`<expr_real>` y `<expr_bool>` y escribir `<declaracion> ::= "entero" ID "=" <expr_entero>
";"`. La gramática crece, pero sigue siendo libre de contexto. El problema aparece cuando
la expresión usa una variable: en `si (y)` o en `x + 1`, el tipo depende de una
declaración que está en otra parte del programa. Es el mismo problema que el de declarar
antes de usar.

### 3. El argumento formal: el lenguaje { *wcw* }

"Toda variable usada debe estar declarada" tiene la misma estructura que

> L = { *w* c *w* | *w* ∈ {a, b}\* }

En un programa, la primera *w* es el nombre en la declaración (`entero abba;`), `c` es
el código intermedio y la segunda *w* es el uso (`abba = 1;`). El programa es válido
solo si las dos *w* son **idénticas**, y pueden ser arbitrariamente largas.

**L no es libre de contexto.** Se demuestra con el lema de bombeo para lenguajes libres
de contexto (Bar-Hillel, Perles y Shamir, 1961). Supongamos que L fuera libre de
contexto, con longitud de bombeo *p*. Tomemos

> s = aᵖ bᵖ c aᵖ bᵖ ∈ L

El lema garantiza que s = uvxyz, con |vxy| ≤ *p* y |vy| ≥ 1, de modo que u vⁱ x yⁱ z ∈ L
para todo i ≥ 0. Tomemos i = 0, es decir, quitemos v e y:

1. **Si v o y contienen la `c`**, la cadena resultante no tiene `c` y no está en L.
2. **Si vxy está entero a un lado de la `c`**, ese lado se acorta y el otro no. Las dos
   mitades quedan de distinto largo y la cadena no está en L.
3. **Si vxy cruza la `c` sin contenerla**, como |vxy| ≤ *p*, v solo puede tocar las b de
   la izquierda e y solo las a de la derecha. Al quitarlas, la izquierda queda con menos
   b o la derecha con menos a, y las mitades dejan de ser iguales.

En los tres casos se llega a una contradicción, así que L no es libre de contexto.

**De { *wcw* } a los programas.** Sea P el lenguaje de los programas válidos y
supongamos que fuera libre de contexto. Su intersección con el lenguaje regular

> R = `entero␣` [ab]⁺ `;imprimir(` [ab]⁺ `);`

también lo sería, porque la intersección de un lenguaje libre de contexto con uno regular
es libre de contexto. Como un programa de R es válido solo si declara la misma variable
que imprime, la intersección es

> P ∩ R = { `entero␣`*w*`;imprimir(`*w*`);` | *w* ∈ {a, b}⁺ }

Ahora aplicamos el homomorfismo *h* que convierte `(` en `c` y borra todos los demás
símbolos que no son a ni b. Las palabras `entero` e `imprimir` no tienen ninguna a ni b,
así que *h*(P ∩ R) = { *wcw* | *w* ∈ {a, b}⁺ }. Los lenguajes libres de contexto son
cerrados bajo homomorfismos, así que este lenguaje también sería libre de contexto. Pero
la demostración anterior funciona igual con *w* no vacía (la cadena *s* elegida tiene
*w* = aᵖbᵖ). Contradicción. Por lo tanto, **ninguna CFG puede describir exactamente los
programas en que toda variable usada fue declarada**.

{ *wcw* } sí es **sensible al contexto** (tipo 1): lo reconoce un autómata linealmente
acotado, que puede recorrer la cinta de ida y vuelta para comparar las dos mitades.

### 4. Por eso existe la tabla de símbolos

Ningún compilador real escribe una gramática sensible al contexto: sería enorme e
ineficiente. La solución estándar divide el trabajo:

- **Una CFG para la estructura.** En nuestro caso, `statements.py` agrupa los tokens y
  reconoce los bloques.
- **Una estructura de datos para el contexto.** Es la tabla de símbolos de
  [compiler/symbol_table.py](compiler/symbol_table.py). Recuerda cada nombre con su tipo:
  `declare()` registra la primera *w* y `lookup()` la compara con la segunda.
- **La pila de ámbitos** refleja el anidamiento de las llaves, que es la parte libre de
  contexto. Los diccionarios de cada ámbito guardan los nombres, que es la parte que la
  CFG no puede ver.

La formalización de este enfoque son las **gramáticas de atributos** (Knuth, 1968): una
CFG cuyas reglas además calculan y verifican información como tipos y nombres declarados.

### 5. Puente a la Fase 2: la concordancia en español

El español tiene el mismo tipo de restricción entre palabras:

> *el perro negro* ✓  ·  \**la perros negro* ✗

El artículo, el sustantivo y el adjetivo deben concordar en género y número. Como esos
rasgos son finitos, una CFG puede manejarlos multiplicando las reglas (`<SN_masc_sing>`,
`<SN_fem_plur>`, …), igual que podía con los tipos de los literales. Pero la gramática
crece rápido, y la concordancia entre palabras alejadas tiene el mismo problema que las
variables declaradas lejos de su uso. Shieber (1985) demostró que el suizo alemán tiene
dependencias cruzadas que ninguna CFG puede describir. En la Fase 2 volveremos a usar la
misma idea: una gramática para la estructura y algo más (rasgos o atributos) para el
contexto.

### Referencias

- Bar-Hillel, Y., Perles, M. y Shamir, E. (1961). On formal properties of simple phrase
  structure grammars. *Zeitschrift für Phonetik, Sprachwissenschaft und
  Kommunikationsforschung*, 14, 143–172.
- Chomsky, N. (1956). Three models for the description of language. *IRE Transactions on
  Information Theory*, 2(3), 113–124.
- Chomsky, N. (1959). On certain formal properties of grammars. *Information and
  Control*, 2(2), 137–167.
- Hopcroft, J. E., Motwani, R. y Ullman, J. D. (2006). *Introduction to Automata Theory,
  Languages, and Computation* (3.ª ed.). Addison-Wesley. Cap. 7: lema de bombeo y
  propiedades de cierre de los lenguajes libres de contexto.
- Knuth, D. E. (1968). Semantics of context-free languages. *Mathematical Systems
  Theory*, 2(2), 127–145.
- Shieber, S. M. (1985). Evidence against the context-freeness of natural language.
  *Linguistics and Philosophy*, 8(3), 333–343.
- Sipser, M. (2013). *Introduction to the Theory of Computation* (3.ª ed.). Cengage
  Learning. Sección 2.3: lenguajes que no son libres de contexto.

## Equipo y responsabilidades

<!-- TODO: reemplazar "Persona N" por los nombres. -->


| Persona   | Responsabilidad                                         | Archivos                                                                          |
| --------- | ------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Persona 1 | Especificación, autómata, reflexión, guion del video | `docs/`                                                                           |
| Persona 2 | Lexer                                                   | `compiler/lexer.py`                                                               |
| Persona 3 | Tabla de símbolos y ámbitos                           | `compiler/symbol_table.py`, secciones P3 de `semantic.py`                         |
| Persona 4 | Sentencias y reglas de tipos                            | `compiler/statements.py`, `compiler/type_rules.py`, secciones P4 de `semantic.py` |
| Persona 5 | Pruebas, repositorio, README, edición del video        | `tests/`, `README.md`                                                             |

### Cronograma


| Día | P1                                    | P2                             | P3                               | P4                             | P5                            |
| ---- | ------------------------------------- | ------------------------------ | -------------------------------- | ------------------------------ | ----------------------------- |
| 1    | Tabla de tokens final                 | Esqueleto del lexer            | Diseño de la tabla de símbolos | Diseño de las reglas de tipos | Repositorio y pytest          |
| 2    | Autómata y borrador de la reflexión | Lexer completo                 | Pila de ámbitos y declaraciones | Agrupación de sentencias      | Pruebas del lexer             |
| 3    | Reflexión terminada                  | Errores léxicos y comentarios | No declaradas y shadowing        | Reglas de tipos                | Pruebas del semántico        |
| 4    | Guion del video                       | Apoyo a la integración        | Integración con P4              | Integración con P3            | Correr todo y reportar fallos |
| 5    | Programas de ejemplo                  | Corrección de errores         | Corrección de errores           | Corrección de errores         | README final                  |
| 6    | Grabación                            | Grabación                     | Grabación                       | Grabación                     | Primer corte del video        |
| 7    | Revisión y entrega                   | Revisar el video               | Revisar el video                 | Revisar el video               | Subir el video                |

**Hitos:** lexer completo el día 3; flujo lexer → semántico el día 4.

### Cómo trabajar sin bloquearse

Mientras el lexer no esté listo, P3 y P4 prueban con tokens escritos a mano:

```python
from helpers import tokens_by_hand
tokens = tokens_by_hand("""
entero x = 1 ;
si ( x > 0 ) {
    real x = 2.5 ;
}
""")
```

Flujo de Git sugerido: una rama por persona (`lexer`, `tabla-simbolos`, `tipos`, `docs`, `tests`),
pull request a `main` y `pytest` antes de cada merge.

## Video

<!-- TODO(P5): enlace al video final. -->

Guion y tiempos en [docs/guion_video.md](docs/guion_video.md).
