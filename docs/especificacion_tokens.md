# Especificación formal de tokens

**Responsable:** Persona 1

<!-- TODO(P1): revisar la tabla, agregar ejemplos y casos borde. La versión final
     debe coincidir con compiler/tokens.py. -->

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

| Token | Expresión regular | Ejemplos | `TokenType` |
| --- | --- | --- | --- |
| Palabras reservadas | `entero`, `real`, `bool`, `si`, `sino`, `mientras`, `imprimir`, `verdadero`, `falso` | `si` | `INT`, `IF`, … |
| ID | `letra (letra \| digito)*` (después de descartar las palabras reservadas) | `x`, `_total2` | `ID` |
| NUM_ENTERO | `digito+` | `0`, `42` | `INT_LITERAL` |
| NUM_REAL | `digito+ \. digito+` | `3.14` | `REAL_LITERAL` |
| Operadores | `==`, `!=`, `<=`, `>=`, `&&`, `\|\|`, `+`, `-`, `*`, `/`, `<`, `>`, `=`, `!` | | `EQUAL`, `AND`, … |
| Delimitadores | `(`, `)`, `{`, `}`, `;`, `,` | | `LPAREN`, `SEMICOLON`, … |
| Comentarios (se ignoran) | `//.*` y `/\*(.\|\n)*?\*/` | | — |
| Espacios (se ignoran) | `[ \t\r\n]+` | | — |

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
3. <!-- TODO(P1): `/` frente a `//` y `/*`. -->

## Errores léxicos

| Entrada | Error |
| --- | --- |
| `@`, `#`, `$`, `&` suelto, `\|` suelto | carácter inválido |
| `12.3.4` | número mal formado |
| `3abc` | identificador que empieza con dígito |
| `/* ...` sin `*/` | comentario sin cerrar |

<!-- TODO(P1): ¿`12.` y `.5` son errores? Acordarlo con P2. -->
