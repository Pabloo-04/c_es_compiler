# Especificación formal de tokens

**Responsable:** Persona 1

## Alfabeto

El alfabeto de entrada del lexer es Σ: los caracteres que pueden aparecer en un
programa **fuera de los comentarios**. Se define como la unión de seis conjuntos
disjuntos:

| Conjunto | Elementos | Cantidad |
| --- | --- | --- |
| Σ<sub>letra</sub> | `a` … `z`, `A` … `Z`, `_` | 53 |
| Σ<sub>dígito</sub> | `0` … `9` | 10 |
| Σ<sub>op</sub> | `+` `-` `*` `/` `<` `>` `=` `!` `&` `\|` | 10 |
| Σ<sub>delim</sub> | `(` `)` `{` `}` `;` `,` | 6 |
| Σ<sub>punto</sub> | `.` | 1 |
| Σ<sub>esp</sub> | espacio, tabulador `\t`, retorno `\r`, salto de línea `\n` | 4 |

```
Σ = Σletra ∪ Σdígito ∪ Σop ∪ Σdelim ∪ Σpunto ∪ Σesp        |Σ| = 84
```

Observaciones:

- **El `_` cuenta como letra.** Puede iniciar un identificador (`_total`), igual que en C.
- **Solo ASCII.** `ñ`, `á` y los demás caracteres acentuados no pertenecen a Σ, así que
  `año` produce un error léxico en la `ñ`. Las palabras reservadas no llevan tilde.
- **`&` y `|` pertenecen a Σ, pero solos no forman ningún token.** Solo son válidos
  duplicados (`&&`, `||`). En rigor, un `&` suelto no es un carácter ajeno a Σ, sino
  una cadena de Σ\* que no está en el lenguaje de ningún token. El lexer lo reporta con
  el mismo mensaje, "carácter inválido '&'", porque para el usuario es el mismo problema.
- **El `.` solo aparece dentro de `NUM_REAL`.** No es un operador. Un `.` suelto
  (como en `.5`) da el mismo error: "carácter inválido '.'".
- **No hay comillas.** `"` y `'` no pertenecen a Σ, porque el lenguaje no tiene cadenas
  de texto en esta fase.

### Alfabeto de los comentarios

Dentro de un comentario se acepta **cualquier carácter** (Unicode completo, incluidas
`ñ` y tildes). Si Γ es el conjunto de todos los caracteres, un programa fuente es una
cadena de Γ\*, y el lexer exige:

- **Fuera de los comentarios:** solo caracteres de Σ. Cualquier carácter de Γ \ Σ da el
  error "carácter inválido".
- **Dentro de `//...` y `/*...*/`:** caracteres de Γ.

```
comentario_linea  = "//" (Γ \ {\n})*
comentario_bloque = "/*" Γ* "*/"    (la menor cadena posible: termina en el primer */)
```

### Dos alfabetos: el del lexer y el del parser

- **Σ, el alfabeto de caracteres.** Es la entrada del lexer: los símbolos de la gramática
  léxica (tipo 3).
- **T, el alfabeto de tokens.** Es la salida del lexer y la entrada de la sintaxis: los
  terminales de la gramática sintáctica (tipo 2) de [gramatica.md](gramatica.md).

```
T = { entero, real, bool, si, sino, mientras, imprimir, verdadero, falso,
      ID, NUM_ENTERO, NUM_REAL,
      ==, !=, <=, >=, &&, ||, +, -, *, /, <, >, =, !,
      (, ), {, }, ;, , }                                         |T| = 32
```

En el código, T es el enum `TokenType` sin `EOF`, y el lexer es la función
Σ\* → T\* (más una lista de errores).

### Definiciones auxiliares

```
letra  = [a-zA-Z_]        (= Σletra)
digito = [0-9]            (= Σdígito)
```

## Tabla de tokens

| Token | Expresión regular | Ejemplos válidos | No es este token | `TokenType` |
| --- | --- | --- | --- | --- |
| Palabras reservadas | `entero` \| `real` \| `bool` \| `si` \| `sino` \| `mientras` \| `imprimir` \| `verdadero` \| `falso` | `si`, `mientras` | `Si`, `entero3`, `sino_` (son ID) | `INT`, `REAL`, `BOOL`, `IF`, `ELSE`, `WHILE`, `PRINT`, `TRUE`, `FALSE` |
| ID | `letra (letra \| digito)*`, si no es palabra reservada | `x`, `_total2`, `enteros` | `3abc`, `año` | `ID` |
| NUM_ENTERO | `digito+` | `0`, `42`, `007` | `-5` (es `-` y `5`) | `INT_LITERAL` |
| NUM_REAL | `digito+ \. digito+` | `3.14`, `0.0` | `12.`, `.5`, `1e3` | `REAL_LITERAL` |
| Igualdad | `==` \| `!=` | | | `EQUAL`, `NOT_EQUAL` |
| Relacionales | `<=` \| `>=` \| `<` \| `>` | | | `LESS_EQUAL`, `GREATER_EQUAL`, `LESS`, `GREATER` |
| Lógicos | `&&` \| `\|\|` \| `!` | | `&`, `\|` sueltos | `AND`, `OR`, `NOT` |
| Aritméticos | `+` \| `-` \| `*` \| `/` | | | `PLUS`, `MINUS`, `STAR`, `SLASH` |
| Asignación | `=` | | | `ASSIGN` |
| Delimitadores | `(` \| `)` \| `{` \| `}` \| `;` \| `,` | | | `LPAREN`, `RPAREN`, `LBRACE`, `RBRACE`, `SEMICOLON`, `COMMA` |
| Comentario de línea (se descarta) | `//[^\n]*` | `// hola` | | — |
| Comentario de bloque (se descarta) | `/\*(.\|\n)*?\*/` | `/* a \n b */` | | — |
| Espacios (se descartan) | `[ \t\r\n]+` | | | — |
| Fin de archivo | (ninguna: lo agrega el lexer) | | | `EOF` |

En total hay 32 tipos de token, más `EOF`.

**Casos borde:**

- **Mayúsculas.** Las palabras reservadas distinguen mayúsculas: `Si` y `ENTERO` son
  identificadores.
- **Ceros a la izquierda.** `007` es un `NUM_ENTERO` válido; su valor es 7.
- **Números negativos.** No hay literales negativos: `-5` son dos tokens, `MINUS` y
  `NUM_ENTERO`. El signo lo maneja la gramática como operador unario
  (ver [gramatica.md](gramatica.md)).
- **Notación científica.** `1e3` no existe: es `NUM_ENTERO` pegado a una letra, y eso es
  un error.
- **Comentarios anidados.** No existen. `/* a /* b */ c */` termina en el primer `*/`, así
  que ` c */` se analiza como código y da `ID` `STAR` `SLASH`.
- **Comentario vacío.** `/**/` es un comentario válido: `a/**/b` da `ID` `ID`.
- **Comentario de línea al final del archivo.** No necesita un `\n` final.
- **Expresiones regulares en el código.** En `compiler/tokens.py` la de los comentarios
  de bloque se escribe `/\*[\s\S]*?\*/`, que es equivalente a la de la tabla, y la de
  línea `//[^\n]*`, equivalente a `//.*`.

## Versión ejecutable

Esta tabla está implementada en `compiler/tokens.py`:

- **`TOKEN_PATTERNS`:** lista de pares (tipo, expresión regular) en orden de prioridad.
- **`MASTER_PATTERN`:** todas las expresiones regulares unidas en una sola.
- **`classify(lexema)`:** devuelve el tipo de un lexema completo.

`tests/test_token_spec.py` verifica que el lexer a mano produce los mismos tokens que
estas expresiones regulares. La gramática en BNF está en [gramatica.md](gramatica.md).

## Reglas de desambiguación

1. **Lexema más largo (maximal munch):** `==` es un token, no dos `=`; `enteros` es un ID, no `entero` + `s`.
2. **Prioridad:** si un lexema encaja como palabra reservada y como ID, gana la palabra reservada.
3. **Comentarios antes que división.** Cuando el lexer ve `/`, mira el carácter
   siguiente (un carácter de lookahead):
   - `//` empieza un comentario de línea.
   - `/*` empieza un comentario de bloque.
   - Cualquier otro carácter: `/` es el operador `SLASH`.

   Es un caso particular del lexema más largo: `//` y `/*` son más largos que `/`. Por
   eso `x/y` da `ID SLASH ID`, `x//y` da solo `ID` (el resto es comentario) y `x/ /y`
   da `ID SLASH SLASH ID`. En `TOKEN_PATTERNS` esta regla se cumple poniendo los
   comentarios antes que los operadores.
4. **Los espacios separan tokens.** `entero x` son dos tokens y `enterox` es un ID.
   Entre dos operadores no hace falta espacio: `x<=-1` da `ID LESS_EQUAL MINUS NUM_ENTERO`.
5. **Consecuencias del lexema más largo con operadores:**
   - `===` da `==` y `=`.
   - `<==` da `<=` y `=`.
   - `&&&` da `&&` y un error por el `&` que sobra.
   - `=!` da `=` y `!`, porque `=!` no es un operador.

## Errores léxicos

El lexer **no se detiene** ante un error: lo reporta con línea y columna y sigue
analizando. Los mensajes tienen el formato común de `compiler/errors.py`:
`Línea 3, columna 14: carácter inválido '@'`.

| Entrada | Mensaje | Qué hace el lexer |
| --- | --- | --- |
| `@`, `#`, `$`, `"`, `ñ`, `á` (caracteres fuera de Σ) | `carácter inválido '@'` | Salta ese carácter y sigue. |
| `&` o `\|` sueltos | `carácter inválido '&'` | Salta ese carácter y sigue. |
| `.5` | `carácter inválido '.'` | Salta el `.` y después lee `5` como `NUM_ENTERO`. |
| `12.` | `número mal formado '12.'` | Consume `12.` completo. |
| `12.3.4`, `12.3.4.5` | `número mal formado '12.3.4'` | Consume el lexema completo y reporta un solo error. |
| `3.5x` | `número mal formado '3.5x'` | Consume el lexema completo. |
| `3abc`, `3_a` | `identificador no puede empezar con dígito: '3abc'` | Consume el lexema completo. |
| `1..2` | `número mal formado '1.'` y `carácter inválido '.'` | Dos errores; después lee `2`. |
| `/* ...` sin `*/` | `comentario sin cerrar` | Reporta la posición donde empezó el `/*` y llega al final del archivo. |

### Decisiones acordadas con P2

- **`12.` es un error.** La expresión regular de `NUM_REAL` exige al menos un dígito
  después del punto. El lexer lo reporta como número mal formado en lugar de leer `12`
  y dejar el `.` suelto, porque es casi seguro un número incompleto.
- **`.5` no es un número.** La expresión regular exige al menos un dígito antes del
  punto. Como `.` no es un token por sí solo, se reporta como carácter inválido y
  después se lee `5`.
- **Un error por lexema mal formado.** En `12.3.4` y `3abc` el lexer consume el lexema
  completo y reporta un solo error. Si no, `3abc` daría `NUM_ENTERO 3` + `ID abc` y el
  semántico mostraría errores confusos.
- **Errores que las expresiones regulares solas no detectan.** Las regex de la tabla
  partirían `3abc` en `3` + `abc` y `12.3.4` en `12.3` + `.` + `4`. Detectarlos
  requiere una regla extra: un número no puede ir seguido de una letra, `_` o `.dígito`.
  Esa regla está en `read_number()` de `compiler/lexer.py`, y en el autómata son los
  estados de error (ver [automata.md](automata.md)).
