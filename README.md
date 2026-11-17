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
│   ├── test_symbol_table.py
│   └── test_semantic.py
├── examples/                  # programas .esp para las demos
└── docs/
    ├── especificacion_tokens.md   # P1
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

La especificación formal y el autómata están en [docs/especificacion_tokens.md](docs/especificacion_tokens.md) y [docs/automata.md](docs/automata.md).

### Sentencias

```
tipo ID ;              tipo ID = expr ;          ID = expr ;
si ( expr ) { ... }    si ( expr ) { ... } sino { ... }
mientras ( expr ) { ... }                        imprimir ( expr ) ;
```

No hay funciones en esta fase: los bloques de `si` y `mientras` bastan para demostrar los ámbitos.

## Reflexión

<!-- TODO(P5): integrar aquí el texto final de docs/reflexion.md (Persona 1). -->

*Pendiente. Borrador en [docs/reflexion.md](docs/reflexion.md).*

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
