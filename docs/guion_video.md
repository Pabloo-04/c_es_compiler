# Guion del video (meta: unos 9 minutos, límite 10)

**Responsable:** Persona 1 · **Edición:** Persona 5

Reglas: todos aparecen y se ve el código ejecutándose, no solo diapositivas.


| # | Segmento          | Quién  | Tiempo | Acumulado |
| - | ----------------- | ------- | ------ | --------- |
| 1 | Lenguaje y tokens | P1      | 1:30   | 1:30      |
| 2 | Lexer             | P2 y P5 | 3:00   | 4:30      |
| 3 | Semántico        | P3 y P4 | 3:30   | 8:00      |
| 4 | Reflexión        | P1      | 1:00   | 9:00      |

## 1. Lenguaje y tokens (P1, 1:30)

Unas 250 palabras. A ritmo normal (unas 160 por minuto) dura alrededor de 1:30. Si al
cronometrar se pasa, recortar primero el bloque 3, que ahorra unos 15 segundos.

### Bloque 1: el lenguaje (0:00–0:20)

> **En pantalla:** [examples/valid.esp](../examples/valid.esp) en el editor.

"Hola. Nuestro compilador trabaja con un lenguaje propio, parecido a C, pero con las
palabras clave en español. Tiene tres tipos de datos, `entero`, `real` y `bool`, y las
sentencias `si`, `sino`, `mientras` e `imprimir`. En esta fase no hay funciones: los
bloques con llaves bastan para mostrar los ámbitos. Antes de analizar este programa, el
compilador tiene que partirlo en piezas: los tokens."

### Bloque 2: alfabeto y tokens (0:20–0:45)

> **En pantalla:** la tabla de tokens de
> [especificacion_tokens.md](especificacion_tokens.md).

"El alfabeto tiene 84 caracteres ASCII: letras, dígitos, operadores, delimitadores y
espacios. Con él definimos 32 tipos de token, cada uno con una expresión regular. Por
ejemplo, un identificador es una letra seguida de letras o dígitos, y un número real son
dígitos, un punto y más dígitos."

### Bloque 3: desambiguación (0:45–1:00)

> **En pantalla:** la misma página, en "Reglas de desambiguación".

"Cuando hay ambigüedad aplicamos dos reglas. Primero, se toma el lexema más largo: `==`
es un solo operador y `enteros` es un identificador, no la palabra `entero` más una `s`.
Segundo, las palabras reservadas ganan sobre los identificadores."

### Bloque 4: el autómata (1:00–1:25)

> **En pantalla:** [img/automata.png](img/automata.png) a pantalla completa. Señalar el
> recorrido con el cursor.

"Estas expresiones regulares se implementan con un autómata finito. Con `3.14`, el
autómata pasa de q0 a q2 con el 3, a q3 con el punto y a q4 con el 1 y el 4; q4 es de
aceptación, así que es un número real. En cambio, `12.` termina en q3, que no acepta, y
`3abc` cae en el estado de error e1. Por el teorema de Kleene, todo lenguaje que reconoce
un autómata finito es regular: los tokens son un lenguaje de tipo 3."

### Bloque 5: código ejecutándose y pase a P2 (1:25–1:30)

> **En pantalla:** la terminal.

```bash
python main.py examples/valid.esp --tokens
```

"Y esta es la tabla de tokens real que produce nuestro lexer. Les explica cómo funciona…"
*(nombre de P2)*.

### Notas para grabar

- Ensayar el recorrido de `3.14` sobre la imagen. Es el momento más visual del segmento.
- Para el bloque 5, dejar el comando escrito de antemano y solo presionar Enter. La salida
  es larga: hacer scroll hasta arriba o mostrar solo las primeras líneas.
- La reflexión (segmento 4) retoma la idea de los lenguajes "tipo 3". No hace falta
  explicar la jerarquía de Chomsky aquí; basta nombrarla.

## 2. Lexer (P2 y P5, 3:00)

Comandos de la demo:

```bash
python main.py examples/valid.esp --lexer-only
python main.py examples/lexical_errors.esp
pytest tests/test_lexer.py -v      # P5
```

<!-- TODO(P1 con P2): texto del diseño del lexer y de cada demo. -->

## 3. Semántico (P3 y P4, 3:30)

```bash
python main.py examples/scopes.esp --simbolos # P3: shadowing
python main.py examples/semantic_errors.esp  # P3 y P4
python main.py examples/valid.esp
pytest -v                                # P5
```

<!-- TODO(P1 con P3 y P4): texto. P3: pila de ámbitos. P4: reglas de tipos. -->

## 4. Reflexión (P1, 1:00)

Unas 160 palabras, alrededor de 1:00. Es la versión hablada de la sección "Reflexión"
del [README](../README.md#reflexión). La demostración completa con el lema de bombeo
queda en el README; aquí solo se da la idea.

### Bloque 1: la jerarquía (0:00–0:15)

> **En pantalla:** la tabla "Cada fase, un nivel de la jerarquía de Chomsky" del README.

"Para cerrar: ¿por qué hace falta un analizador semántico? Cada fase corresponde a un
nivel de la jerarquía de Chomsky. Los tokens son regulares: basta un autómata finito. Las
llaves anidadas son libres de contexto: necesitan una pila."

### Bloque 2: lo que la CFG no puede ver (0:15–0:30)

> **En pantalla:** [examples/semantic_errors.esp](../examples/semantic_errors.esp),
> señalando `z = 3;`.

"Pero este programa respeta la gramática y aun así está mal: usa `z` sin declararla. Para
detectarlo hay que comparar el nombre usado con uno escrito antes, a cualquier distancia."

### Bloque 3: el argumento formal (0:30–0:45)

> **En pantalla:** "L = { w c w }" y el ejemplo `entero abba; imprimir(abba);`.

"Formalmente, 'declarar antes de usar' tiene la forma w c w: el mismo nombre dos veces,
con código en el medio. Con el lema de bombeo se demuestra que w c w no es libre de
contexto. Por lo tanto, ninguna gramática libre de contexto puede expresar esta regla."

### Bloque 4: la solución y el cierre (0:45–1:00)

> **En pantalla:** la terminal.

```bash
python main.py examples/semantic_errors.esp
```

"Por eso usamos una tabla de símbolos, que guarda cada nombre con su tipo y su ámbito.
El español tiene un problema parecido: en 'el perro negro' las palabras deben concordar.
Ese es el punto de partida de la Fase 2. Gracias."

### Notas para grabar

- El bloque 4 necesita el semántico de P3 y P4 terminado. Si no está listo para la
  grabación, mostrar la tabla de símbolos con `--simbolos` sobre
  [examples/scopes.esp](../examples/scopes.esp) en cuanto funcione, o grabar esta parte
  al final.
- No leer la demostración del lema de bombeo en voz alta: no entra en un minuto. Basta
  decir que existe y que está en el README.
- La palabra clave del segmento es "comparar": el autómata y la pila no pueden comparar
  dos nombres arbitrariamente largos; la tabla de símbolos sí.

## Checklist de grabación

- [X]  Terminal con letra grande y fondo legible.
- [X]  Probar todos los comandos antes de grabar.
- [X]  Cronometrar cada segmento.
- [X]  Duración final < 10:00.
