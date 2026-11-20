# Compilador Fase 1: lexer y analizador semántico

**Integrantes:**

* Pablo Vides 00080323
* Gabriela Valiente
* Valeria Ortiz
* Paola Pérez Pérez 00117222
* Alejandro Melgar

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

- Python 3.10 o superior (se usa `match` y la sintaxis `X | None`).
- Git.

```bash
git clone https://github.com/Pabloo-04/c_es_compiler.git
cd c_es_compiler
git checkout develop               # rama con el trabajo integrado

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt     # solo pytest; el compilador no tiene dependencias
```

Para comprobar que todo quedó bien instalado:

```bash
pytest -q                          # deben pasar todas las pruebas
python main.py examples/valid.esp  # "Programa correcto: sin errores léxicos ni semánticos."
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

Si hay errores léxicos no se corre el semántico.

Código de salida: `0` sin errores (puede haber advertencias), `1` con errores y `2`
si no se pudo leer el archivo.

## Pruebas

```bash
pytest                             # todas
pytest -v                          # con el nombre de cada prueba
pytest -v tests/test_lexer.py      # un solo archivo
pytest -k shadowing                # solo las pruebas cuyo nombre contiene "shadowing"
```

Cada archivo cubre una parte del compilador, con entradas válidas e inválidas:

| Archivo | Qué prueba | Autor |
| --- | --- | --- |
| `tests/test_lexer.py` | Tokens, posiciones, comentarios, palabras reservadas y errores léxicos (`@`, `12.3.4`, `3abc`, `&` suelto, comentario sin cerrar) | P5 |
| `tests/test_lexerV2.py` | Casos borde del lexer: `12.`, `.5`, `3.5x`, columnas de error, entradas basura | P2 |
| `tests/test_token_spec.py` | El lexer coincide con las expresiones regulares de la especificación | P1 |
| `tests/test_errors.py` | Formato único `Línea N, columna M: ...` y jerarquía de errores | P1 |
| `tests/test_symbol_table.py` | Pila de ámbitos: declarar, buscar, redeclarar, shadowing, tres niveles, cerrar el ámbito global | P5 |
| `tests/test_semantic.py` | No declaradas, redeclaraciones, ámbitos, llaves desbalanceadas, reglas de tipos, varios errores en un programa | P5 |
| `tests/test_p4_types.py` | Agrupación en sentencias, tabla de tipos, precedencia, mensajes sin errores en cascada | P4 |
| `tests/test_integration.py` | Lexer + semántico sobre cada `examples/*.esp`, y `main.py` (opciones y códigos de salida 0, 1 y 2) | P5 |

`tests/helpers.py` tiene `tokens_by_hand()`, que arma tokens a mano para probar el
semántico sin depender del lexer.

## Estructura del proyecto

```
c_es_compiler/
├── main.py                    # CLI: lee el archivo, corre las dos fases y muestra el resultado
├── requirements.txt           # pytest
├── pytest.ini
├── compiler/
│   ├── tokens.py              # Token y TokenType: contrato compartido
│   ├── errors.py              # errores y advertencias: formato común
│   ├── lexer.py               # P2
│   ├── symbol_table.py        # P3
│   ├── statements.py          # P4: agrupar tokens en sentencias
│   ├── type_rules.py          # P4: reglas de tipos
│   └── semantic.py            # P3 + P4: orquesta el análisis
├── tests/
│   ├── helpers.py             # tokens_by_hand(): tokens sin depender del lexer
│   ├── test_errors.py
│   ├── test_lexer.py
│   ├── test_lexerV2.py
│   ├── test_token_spec.py
│   ├── test_symbol_table.py
│   ├── test_semantic.py
│   ├── test_p4_types.py
│   └── test_integration.py
├── examples/                  # programas .esp para las demos
│   ├── valid.esp              # sin errores
│   ├── scopes.esp             # ámbitos anidados y shadowing (válido, con advertencias)
│   ├── lexical_errors.esp     # un error léxico por línea marcada
│   ├── semantic_errors.esp    # un error semántico por línea marcada
│   └── demo_p3.esp            # demo de la tabla de símbolos
└── docs/
    ├── especificacion_tokens.md   # P1
    ├── gramatica.md               # gramática en BNF y EBNF
    ├── automata.md                # P1
    ├── reflexion.md               # P1
    └── guion_video.md             # P1
```

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

Advertencias: variable declarada pero nunca usada, shadowing (una variable oculta a
otra de un ámbito externo) y uso sin inicializar. Si hay errores léxicos, `main.py` no corre el semántico.

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
| `== !=` entre números o entre `bool` | `bool`         |
| `&& \|\|` entre `bool`, `!bool`        | `bool`         |
| `-entero`, `-real` (menos unario)    | el mismo tipo  |
| condición de `si` / `mientras`      | debe ser `bool` |

Cualquier otra combinación es un error (`operación inválida: entero && bool`).

**Asignación:** el valor debe ser del mismo tipo que la variable, con una excepción:
un `entero` se puede guardar en un `real` (`real x = 5;` es válido), pero no al revés
(`entero x = 2.5;` da `no se puede asignar real a entero`, porque perdería los decimales).

El tipo de una expresión se calcula en `type_rules.expression_type()` con descenso
recursivo: una función por nivel de precedencia de [docs/gramatica.md](docs/gramatica.md).
Un mismo problema genera un solo error: si una subexpresión ya es inválida, las
operaciones que la contienen no agregan más mensajes.

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

*Este texto también está en [docs/reflexion.md](docs/reflexion.md).*

### 1. Cada fase, un nivel de la jerarquía de Chomsky

| Fase | Tipo de lenguaje | Reconocedor | En nuestro código |
| --- | --- | --- | --- |
| Lexer | Regular (tipo 3) | Autómata finito | `compiler/lexer.py` |
| Parser | Libre de contexto (tipo 2) | Autómata de pila | `docs/gramatica.md` (Fase 2) |
| Semántico | Sensible al contexto (tipo 1) | Tabla de símbolos (más memoria que una pila) | `compiler/semantic.py`, `compiler/symbol_table.py` |

**Los tokens son regulares.** Cada token se describe con una expresión regular
(`[a-zA-Z_][a-zA-Z0-9_]*`, `[0-9]+\.[0-9]+`, ...) y la unión de todas ellas también es
regular. Por eso basta un autómata finito ([automata.md](docs/automata.md)). Para decidir
el token, el lexer solo necesita saber en qué estado está, no lo que leyó antes. Su
memoria es finita y no depende del largo del programa.

**Los bloques balanceados ya no son regulares.** Un programa puede anidar
`si (...) { mientras (...) { ... } }` a cualquier profundidad, y cada `{` debe
cerrarse con su `}`. Ese patrón es el lenguaje { `{`ⁿ `}`ⁿ | n ≥ 0 }. Por el lema de
bombeo para lenguajes regulares no es regular. Con la cadena `{`ᵖ `}`ᵖ, la parte
bombeable cae dentro de las `{` iniciales, y al repetirla quedan más `{` que `}`.
Un autómata finito no puede contar hasta un n arbitrario. Hace falta una **pila**,
es decir, una gramática libre de contexto: `<bloque> ::= "{" <sentencias> "}"`.

**Pero la pila tampoco alcanza para todo.** La CFG describe la *forma* de un programa,
no su *significado*. Las reglas de la siguiente sección relacionan partes del programa
que pueden estar arbitrariamente lejos entre sí, y eso exige más poder que un autómata
de pila.

### 2. Verificaciones del semántico que una CFG no expresa

Los programas siguientes se derivan sin problema de la gramática de
[gramatica.md](docs/gramatica.md), pero el analizador semántico los rechaza.

- **Declaración antes del uso.**

  ```c
  entero contador = 0;
  ...                 // cualquier cantidad de código
  contdor = contador + 1;   // Línea N, columna 1: variable 'contdor' no declarada
  ```

  La regla `<asignacion> ::= ID "=" <expresion> ";"` acepta *cualquier* `ID`. Para
  rechazar `contdor`, hay que comparar ese nombre letra por letra con todos los
  nombres declarados antes, que pueden estar a cualquier distancia.

- **No redeclarar en el mismo ámbito.**

  ```c
  entero y = 1;
  entero y = 2;       // variable 'y' ya declarada en este ámbito (línea 1)
  ```

  Dos `<declaracion>` seguidas son válidas para la gramática. Detectar el error es lo
  mismo que en el caso anterior, pero al revés: hay que reconocer que dos cadenas
  arbitrarias son *iguales*. Y además depende del ámbito: dentro de un bloque
  `real y = 2.5;` sí es válido (shadowing).

- **Concordancia de tipos.**

  ```c
  bool activo = verdadero;
  ...
  entero x = activo;  // no se puede asignar bool a entero
  ```

  Con literales, una CFG *podría* separar expresiones por tipo (`<expr_entera>`,
  `<expr_bool>`, ...). Pero con variables el tipo de `activo` no está escrito en la
  línea donde se usa: está en su declaración, en otra parte del programa. Saber el
  tipo de la expresión es otra vez recordar qué nombre se declaró con qué tipo. Por
  eso `type_rules.expression_type()` consulta la tabla de símbolos.

Las tres reglas comparten la misma forma: **una cadena que aparece en un lugar
condiciona lo que es válido en otro lugar arbitrariamente lejano.** Es la definición
informal de *sensible al contexto*.

### 3. El argumento formal: { wcw }

Reducimos la regla "toda variable usada debe estar declarada" a su forma mínima:

L = { *w* c *w* | *w* ∈ {a, b}\* }

La primera *w* es el nombre en la declaración (`entero w;`), `c` es todo el código de
en medio, y la segunda *w* es el uso (`w = 1;`). El programa es correcto solo si los
dos nombres son idénticos.

**Teorema.** L no es libre de contexto.

**Demostración (lema de bombeo para lenguajes libres de contexto).** Supongamos que L
es libre de contexto, con longitud de bombeo *p*. Tomamos

s = aᵖ bᵖ c aᵖ bᵖ ∈ L,  |s| ≥ p.

El lema garantiza una descomposición s = *uvxyz* con |*vxy*| ≤ *p*, |*vy*| ≥ 1, y
*uvⁱxyⁱz* ∈ L para todo i ≥ 0. Revisamos dónde puede caer *vxy*:

1. **v o y contiene la `c`.** Con i = 0 la cadena queda sin `c` y no está en L, que
   exige exactamente una.
2. **vxy está entero a un lado de la `c`.** Bombear (i = 0 o i = 2) cambia la
   longitud de esa mitad y deja la otra igual. Las dos mitades quedan de distinto
   largo, así que no pueden ser la misma *w*.
3. **vxy cruza la `c`, pero v e y no la contienen.** Como |*vxy*| ≤ *p*, *v* cae en
   el bloque bᵖ de la izquierda y *y* en el bloque aᵖ de la derecha. Con i = 0 queda
   aᵖ bᵖ⁻ʲ c aᵖ⁻ᵏ bᵖ, con j + k ≥ 1. La mitad izquierda termina con menos b o la
   derecha empieza con menos a, así que las mitades ya no son iguales.

En todos los casos alguna cadena bombeada sale de L. Eso contradice el lema, así que
**L no es libre de contexto**. ∎

Sí es **sensible al contexto**. Un autómata linealmente acotado lo reconoce: recorre
la cinta marcando un símbolo de la izquierda y el correspondiente de la derecha,
usando solo el espacio de la propia entrada.

**De L a nuestro lenguaje.** Los lenguajes libres de contexto son cerrados bajo
intersección con lenguajes regulares y bajo homomorfismos. El procedimiento tiene dos
pasos:

1. Se intersecta el conjunto de programas *válidos* con el lenguaje regular
   `entero [ab]+;[ab]+=1;`. Quedan solo los programas `entero w;w=1;` en los que los
   dos nombres coinciden.
2. Se aplica el homomorfismo que borra `entero`, `=` y `1` y convierte cada `;` en
   `c`. Se obtiene { *w* c *w* c }, que tampoco es libre de contexto. El argumento de
   bombeo anterior se aplica igual.

Si los programas válidos fueran libres de contexto, ese resultado también lo sería. Por lo tanto **ninguna CFG puede describir exactamente los programas
semánticamente correctos de nuestro lenguaje.**

### 4. Por eso existe la tabla de símbolos

Si la gramática no puede imponer la regla, alguien más tiene que hacerlo. Por eso el
compilador se divide en fases. El parser (CFG) acepta un superconjunto: todo lo que
tiene la forma correcta. El análisis semántico filtra con memoria adicional.

Esa memoria es `SymbolTable` en
[compiler/symbol_table.py](compiler/symbol_table.py): una **pila de
diccionarios**, uno por ámbito.

| Evento en el programa | Operación | Qué resuelve |
| --- | --- | --- |
| `{` | `open_scope()` | Entra a un ámbito nuevo |
| `entero x = ...;` | `declare(symbol)` | Guarda la primera *w*. Si ya existe en el ámbito actual: redeclaración |
| `x = ...;` o `x` en una expresión | `lookup("x")` | Compara con la *w* guardada. Si no aparece: no declarada |
| `}` | `close_scope()` | Las variables del bloque dejan de existir |

La diferencia con el autómata de pila es la clave. Un autómata de pila solo ve el
**tope**, y al leerlo lo saca. `lookup()` recorre **todos** los ámbitos, del más
interno al global, sin destruir nada. Además compara nombres de longitud arbitraria
contra todos los nombres guardados. Ese acceso libre a lo que ya se leyó es
justamente lo que la demostración de la sección 3 prueba que una CFG no tiene.

El shadowing muestra que la regla depende del contexto. `real x = 2.5;` es un error
si ya hay una `x` en el **mismo** ámbito, pero es válido si la otra `x` está en un
ámbito **externo**. La misma cadena es correcta o incorrecta según dónde aparece.

### 5. Puente a la Fase 2: la concordancia en español

El español tiene el mismo problema que la regla de declaración y uso:

- **el perro negro** es correcto.
- \***la perro negros** es incorrecto: el artículo, el sustantivo y el adjetivo deben
  concordar en género y número.

Es la misma estructura que `entero x = verdadero;`. Un rasgo fijado en una palabra
(el género de *perro*, el tipo de `x`) restringe lo que es válido en otra.

Hay un matiz importante. El género y el número toman pocos valores (masculino o
femenino, singular o plural), así que la concordancia *local* sí cabe en una CFG.
Basta multiplicar los no terminales: `SN_masc_sg`, `SN_fem_pl`, etc. El costo es que
la gramática crece por cada rasgo y cada combinación. Con varios rasgos (género,
número, persona, tiempo) el tamaño explota. Por eso es más limpio dejar la CFG
simple y verificar la concordancia en una fase aparte, como hicimos con los tipos.

Cuando la dependencia es a distancia, como en *"**Las casas** que construyó mi abuelo
en el pueblo **están** pintadas"*, o cuando se cruza, como en las dependencias
seriales cruzadas que Shieber (1985) mostró en el alemán suizo, el lenguaje natural
sale de verdad de los libres de contexto. Pasa lo mismo que con { *w* c *w* }.

En la Fase 2 vamos a reutilizar esta idea. El parser del español usará una CFG para la
estructura (sujeto, verbo, objeto, modificadores), y una fase semántica, con una
tabla de rasgos análoga a la tabla de símbolos, verificará la concordancia. Esa
frontera también nos dará un criterio concreto para comparar el parser formal con
spaCy, HuggingFace y un LLM.

## Equipo y responsabilidades

| Persona | Integrante | Responsabilidad | Archivos |
| --- | --- | --- | --- |
| P1 | Pablo Vides | Especificación, autómata, errores, `main.py`, guion del video | `docs/`, `compiler/tokens.py`, `compiler/errors.py`, `main.py` |
| P2 | Gabriela Valiente | Lexer | `compiler/lexer.py` |
| P3 | Valeria Ortiz | Tabla de símbolos y ámbitos | `compiler/symbol_table.py`, secciones P3 de `semantic.py` |
| P4 | Paola Pérez Pérez | Sentencias y reglas de tipos | `compiler/statements.py`, `compiler/type_rules.py`, secciones P4 de `semantic.py` |
| P5 | Alejandro Melgar | Pruebas, repositorio, README, reflexión en el README, edición del video | `tests/`, `README.md`, `docs/reflexion.md` |

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

### Flujo de Git

- `main`: versión entregada.
- `develop`: integración. Todo el trabajo entra aquí por pull request.
- Una rama por tarea, creada desde `develop`: `feature/lexer`, `feat/semantic_symbol`,
  `feature/semantic_analisis`, `feature/utils`, `feature/tests`, `feature/readme`.

Antes de abrir un pull request hay que correr `pytest` y comprobar que pasa completo.

## Video

**Enlace:** *(pendiente: se agrega cuando el video esté subido)*

Guion y tiempos en [docs/guion_video.md](docs/guion_video.md).
