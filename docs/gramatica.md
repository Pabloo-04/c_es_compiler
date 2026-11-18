# Gramática del lenguaje

Este documento define formalmente el lenguaje de la Fase 1 en dos niveles:

1. **Gramática léxica:** cómo se forman los tokens. Es una gramática regular (tipo 3).
2. **Gramática sintáctica:** cómo se combinan los tokens en un programa. Es libre de contexto (tipo 2).

Cada nivel está en dos notaciones: **BNF pura** (`<no-terminal> ::= ...`, solo con `|`
y recursión) y **EBNF**, más compacta, con `{ x }` (cero o más), `[ x ]` (opcional)
y `( x | y )` (agrupación).

La versión ejecutable de la gramática léxica es `TOKEN_PATTERNS` en
[compiler/tokens.py](../compiler/tokens.py). La sintaxis la recorre, en forma
simplificada, [compiler/statements.py](../compiler/statements.py).

**Convenciones:** los terminales van entre comillas (`"si"`, `";"`) o en MAYÚSCULAS
cuando son tokens con lexema variable (`ID`, `NUM_ENTERO`, `NUM_REAL`).

---

## 1. Gramática léxica

### BNF pura

```bnf
<letra>       ::= "a" | "b" | ... | "z" | "A" | "B" | ... | "Z" | "_"
<digito>      ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

<id>          ::= <letra> | <id> <letra> | <id> <digito>
<num_entero>  ::= <digito> | <num_entero> <digito>
<num_real>    ::= <num_entero> "." <num_entero>

<palabra_reservada> ::= "entero" | "real" | "bool" | "si" | "sino" | "mientras"
                      | "imprimir" | "verdadero" | "falso"

<operador>    ::= "==" | "!=" | "<=" | ">=" | "&&" | "||"
                | "+" | "-" | "*" | "/" | "<" | ">" | "=" | "!"
<delimitador> ::= "(" | ")" | "{" | "}" | ";" | ","
```

Las reglas de `<id>` y `<num_entero>` son **lineales por la izquierda** (el no-terminal
siempre va al principio del lado derecho). Toda gramática lineal por la izquierda es
regular, y por eso la reconoce un autómata finito: el de [automata.md](automata.md).

`<num_real>` usa `<num_entero>` dos veces, así que no es lineal tal como está escrita.
Aun así, el lenguaje que genera es regular, porque es la concatenación de dos lenguajes
regulares. Una forma lineal equivalente es:

```bnf
<num_real>    ::= <parte_entera> "." <digito> | <num_real> <digito>
<parte_entera> ::= <digito> | <parte_entera> <digito>
```

### EBNF y expresiones regulares

| Token | EBNF | Expresión regular | `TokenType` |
| --- | --- | --- | --- |
| `ID` | `letra { letra \| digito }` | `[a-zA-Z_][a-zA-Z0-9_]*` | `ID` |
| `NUM_ENTERO` | `digito { digito }` | `[0-9]+` | `INT_LITERAL` |
| `NUM_REAL` | `digito { digito } "." digito { digito }` | `[0-9]+\.[0-9]+` | `REAL_LITERAL` |
| Espacio (se descarta) | `( " " \| "\t" \| "\r" \| "\n" ) { ... }` | `[ \t\r\n]+` | — |
| Comentario de línea | `"//" { cualquier carácter menos "\n" }` | `//[^\n]*` | — |
| Comentario de bloque | `"/*" { cualquier carácter } "*/"` (el primer `*/` lo cierra) | `/\*[\s\S]*?\*/` | — |

### Reglas que la gramática sola no expresa

La gramática léxica es **ambigua**. `enteros` se puede leer como `entero` + `s`, y
`==` como `=` + `=`. El lexer resuelve la ambigüedad con dos reglas:

1. **Lexema más largo:** se toma el token más largo posible (`==`, `enteros`, `3.14`).
2. **Prioridad:** si un lexema completo es palabra reservada y también `ID`, gana la
   palabra reservada.

Además el lexer agrega reglas de error que no salen de la gramática:

- `3abc`: un número no puede ir pegado a una letra o `_`.
- `12.3.4` y `12.`: números mal formados.
- Un comentario `/*` sin cerrar.

---

## 2. Gramática sintáctica

### BNF pura

```bnf
<programa>         ::= <lista_sentencias>

<lista_sentencias> ::= <sentencia> <lista_sentencias>
                     | ε

<sentencia>        ::= <declaracion>
                     | <asignacion>
                     | <si>
                     | <mientras>
                     | <imprimir>
                     | <bloque>

<declaracion>      ::= <tipo> ID ";"
                     | <tipo> ID "=" <expresion> ";"

<tipo>             ::= "entero" | "real" | "bool"

<asignacion>       ::= ID "=" <expresion> ";"

<si>               ::= "si" "(" <expresion> ")" <bloque>
                     | "si" "(" <expresion> ")" <bloque> "sino" <bloque>

<mientras>         ::= "mientras" "(" <expresion> ")" <bloque>

<imprimir>         ::= "imprimir" "(" <expresion> ")" ";"

<bloque>           ::= "{" <lista_sentencias> "}"

<expresion>        ::= <expr_o>

<expr_o>           ::= <expr_o> "||" <expr_y>
                     | <expr_y>

<expr_y>           ::= <expr_y> "&&" <expr_igualdad>
                     | <expr_igualdad>

<expr_igualdad>    ::= <expr_igualdad> <op_igualdad> <expr_relacional>
                     | <expr_relacional>

<expr_relacional>  ::= <expr_relacional> <op_relacional> <expr_aditiva>
                     | <expr_aditiva>

<expr_aditiva>     ::= <expr_aditiva> <op_aditivo> <expr_multiplicativa>
                     | <expr_multiplicativa>

<expr_multiplicativa> ::= <expr_multiplicativa> <op_multiplicativo> <expr_unaria>
                        | <expr_unaria>

<expr_unaria>      ::= "!" <expr_unaria>
                     | "-" <expr_unaria>
                     | <primaria>

<primaria>         ::= ID
                     | NUM_ENTERO
                     | NUM_REAL
                     | "verdadero"
                     | "falso"
                     | "(" <expresion> ")"

<op_igualdad>      ::= "==" | "!="
<op_relacional>    ::= "<" | ">" | "<=" | ">="
<op_aditivo>       ::= "+" | "-"
<op_multiplicativo> ::= "*" | "/"
```

### EBNF

```ebnf
programa        = { sentencia } ;
sentencia       = declaracion | asignacion | si | mientras | imprimir | bloque ;

declaracion     = tipo ID [ "=" expresion ] ";" ;
tipo            = "entero" | "real" | "bool" ;
asignacion      = ID "=" expresion ";" ;
si              = "si" "(" expresion ")" bloque [ "sino" bloque ] ;
mientras        = "mientras" "(" expresion ")" bloque ;
imprimir        = "imprimir" "(" expresion ")" ";" ;
bloque          = "{" { sentencia } "}" ;

expresion       = expr_y { "||" expr_y } ;
expr_y          = expr_igualdad { "&&" expr_igualdad } ;
expr_igualdad   = expr_relacional { ( "==" | "!=" ) expr_relacional } ;
expr_relacional = expr_aditiva { ( "<" | ">" | "<=" | ">=" ) expr_aditiva } ;
expr_aditiva    = expr_mult { ( "+" | "-" ) expr_mult } ;
expr_mult       = expr_unaria { ( "*" | "/" ) expr_unaria } ;
expr_unaria     = ( "!" | "-" ) expr_unaria | primaria ;
primaria        = ID | NUM_ENTERO | NUM_REAL | "verdadero" | "falso"
                | "(" expresion ")" ;
```

La versión EBNF no tiene recursión por la izquierda, así que se traduce directo a un
analizador de descenso recursivo: una función por regla y un `while` por cada `{ }`.
Es la forma recomendada para `type_rules.expression_type()` (P4).

### Precedencia y asociatividad

La precedencia sale de la gramática: cuanto más abajo está la regla, más fuerte liga
el operador.

| Nivel | Operadores | Asociatividad | Regla |
| --- | --- | --- | --- |
| 1 (más débil) | `\|\|` | izquierda | `<expr_o>` |
| 2 | `&&` | izquierda | `<expr_y>` |
| 3 | `==` `!=` | izquierda | `<expr_igualdad>` |
| 4 | `<` `>` `<=` `>=` | izquierda | `<expr_relacional>` |
| 5 | `+` `-` | izquierda | `<expr_aditiva>` |
| 6 | `*` `/` | izquierda | `<expr_multiplicativa>` |
| 7 (más fuerte) | `!` `-` (unarios) | derecha | `<expr_unaria>` |

La asociatividad por la izquierda viene de la recursión por la izquierda en BNF:
`a - b - c` se agrupa como `(a - b) - c`.

### Ejemplo de derivación

Derivación por la izquierda de `entero x = 1 + 2 * 3;`, abreviando los pasos que solo
bajan de nivel en la cadena de expresiones:

```
<programa>
⇒ <lista_sentencias>
⇒ <sentencia> <lista_sentencias>
⇒ <declaracion> <lista_sentencias>
⇒ <tipo> ID "=" <expresion> ";" <lista_sentencias>
⇒ "entero" ID "=" <expresion> ";" <lista_sentencias>
⇒* "entero" ID "=" <expr_aditiva> ";" <lista_sentencias>
⇒ "entero" ID "=" <expr_aditiva> "+" <expr_multiplicativa> ";" <lista_sentencias>
⇒* "entero" ID "=" NUM_ENTERO "+" <expr_multiplicativa> ";" <lista_sentencias>
⇒ "entero" ID "=" NUM_ENTERO "+" <expr_multiplicativa> "*" <expr_unaria> ";" <lista_sentencias>
⇒* "entero" ID "=" NUM_ENTERO "+" NUM_ENTERO "*" NUM_ENTERO ";" <lista_sentencias>
⇒ "entero" ID "=" NUM_ENTERO "+" NUM_ENTERO "*" NUM_ENTERO ";"
```

El `*` queda más abajo en el árbol que el `+`, así que se evalúa primero: `1 + (2 * 3)`.

### Decisiones de diseño

- **`sino` sin ambigüedad.** Como `si` y `sino` exigen un `<bloque>` con llaves, no
  existe el problema del *dangling else* de C. Por la misma razón no hay `sino si`
  directo: hay que escribir `sino { si (...) { ... } }`.
- **Bloques sueltos.** `<bloque>` también es una sentencia, así que `{ ... }` solo
  abre un ámbito nuevo. Sirve para demostrar el shadowing.
- **La coma `,`** es un token válido, pero ninguna regla la usa todavía. Queda
  reservada para las funciones de la Fase 2.
- **Asignación y declaración.** `=` es una sentencia, no una expresión: `x = y = 1;`
  no es válido.
- **Representación en el código.** No hay parser completo en esta fase.
  `statements.group()` reconoce la forma de cada `<sentencia>` y trata `{` y `}` como
  marcas de ámbito (`OPEN_BLOCK` y `CLOSE_BLOCK`) en una lista plana.

---

## 3. Lo que la gramática NO captura

Todos estos programas son **sintácticamente correctos**: se derivan de la gramática.
Aun así son incorrectos, y los rechaza el análisis semántico:

| Programa | Por qué la CFG lo acepta | Quién lo rechaza |
| --- | --- | --- |
| `x = 5;` sin declarar `x` | `<asignacion> ::= ID "=" <expresion> ";"` acepta cualquier `ID` | Tabla de símbolos (P3) |
| `entero x; entero x;` | Dos `<declaracion>` seguidas son válidas | Tabla de símbolos (P3) |
| `entero x = verdadero;` | `<expresion>` no distingue tipos | Reglas de tipos (P4) |
| `si (1 + 2) { }` | La condición es cualquier `<expresion>` | Reglas de tipos (P4) |
| `bool b = 1 < 2 < 3;` | `<expr_relacional>` es recursiva | Reglas de tipos (P4): `bool < entero` |

Para verificar "toda variable usada fue declarada antes" hay que recordar una cadena
arbitraria (el nombre) y compararla con otra que aparece más adelante. Es el lenguaje
{ *wcw* }, que no es libre de contexto. La explicación completa está en
[reflexion.md](reflexion.md).
