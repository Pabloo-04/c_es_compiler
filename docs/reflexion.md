# Reflexión: lo que una gramática libre de contexto no puede expresar

## 1. Cada fase, un nivel de la jerarquía de Chomsky

| Fase | Tipo de lenguaje | Reconocedor | En nuestro código |
| --- | --- | --- | --- |
| Lexer | Regular (tipo 3) | Autómata finito | `compiler/lexer.py` |
| Parser | Libre de contexto (tipo 2) | Autómata de pila | `docs/gramatica.md` (Fase 2) |
| Semántico | Sensible al contexto (tipo 1) | Tabla de símbolos (más memoria que una pila) | `compiler/semantic.py`, `compiler/symbol_table.py` |

**Los tokens son regulares.** Cada token se describe con una expresión regular
(`[a-zA-Z_][a-zA-Z0-9_]*`, `[0-9]+\.[0-9]+`, ...) y la unión de todas ellas también es
regular. Por eso basta un autómata finito ([automata.md](automata.md)). Para decidir
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

## 2. Verificaciones del semántico que una CFG no expresa

Los programas siguientes se derivan sin problema de la gramática de
[gramatica.md](gramatica.md), pero el analizador semántico los rechaza.

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

## 3. El argumento formal: { wcw }

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

## 4. Por eso existe la tabla de símbolos

Si la gramática no puede imponer la regla, alguien más tiene que hacerlo. Por eso el
compilador se divide en fases. El parser (CFG) acepta un superconjunto: todo lo que
tiene la forma correcta. El análisis semántico filtra con memoria adicional.

Esa memoria es `SymbolTable` en
[compiler/symbol_table.py](../compiler/symbol_table.py): una **pila de
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

## 5. Puente a la Fase 2: la concordancia en español

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
