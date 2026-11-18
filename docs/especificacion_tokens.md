# Especificación formal de tokens

**Responsable:** Persona 1

<!-- TODO(P1): revisar la tabla, agregar ejemplos y casos borde. La versión final
     debe coincidir con compiler/tokens.py. -->

## Alfabeto

<!-- TODO(P1): definir Σ (letras, dígitos, operadores, delimitadores, espacios). -->

Definiciones auxiliares:

```
letra  = [a-zA-Z_]
digito = [0-9]
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
