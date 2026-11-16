# Reflexión: lo que una gramática libre de contexto no puede expresar

**Responsable:** Persona 1 · **Integración en el README:** Persona 5

<!-- TODO(P1): redactar cada sección. Al terminar, P5 copia el texto final en
     la sección "Reflexión" del README. -->

## 1. Cada fase, un nivel de la jerarquía de Chomsky

| Fase | Tipo de lenguaje | Reconocedor |
| --- | --- | --- |
| Lexer | Regular (tipo 3) | Autómata finito |
| Parser | Libre de contexto (tipo 2) | Autómata de pila |
| Semántico | Sensible al contexto (tipo 1) | Tabla de símbolos (más memoria que una pila) |

<!-- TODO(P1): explicar por qué los tokens son regulares y por qué los paréntesis
     y llaves balanceados necesitan una pila (ya no son regulares). -->

## 2. Verificaciones del semántico que una CFG no expresa

<!-- TODO(P1): explicar cada una con un ejemplo en nuestro lenguaje. -->

- **Declaración antes del uso:**
- **No redeclarar en el mismo ámbito:**
- **Concordancia de tipos** (`entero x = verdadero;`):

## 3. El argumento formal: {wcw}

<!-- TODO(P1): "Toda variable usada debe estar declarada" se parece a
     L = { wcw | w ∈ {a,b}* }: la primera w es la declaración y la segunda el uso.
     Demostrar con el lema de bombeo para CFL que L no es libre de contexto. -->

## 4. Por eso existe la tabla de símbolos

<!-- TODO(P1): conectar con compiler/symbol_table.py. -->

## 5. Puente a la Fase 2: la concordancia en español

<!-- TODO(P1): "el perro negro" / *"la perro negros": género y número deben
     concordar entre palabras alejadas, el mismo problema que tipo/variable. -->
