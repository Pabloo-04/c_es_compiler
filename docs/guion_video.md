# Guion del video (meta: unos 9 minutos, límite 10)

**Responsable:** Persona 1 · **Edición:** Persona 5

Reglas: todos aparecen y se ve el código ejecutándose, no solo diapositivas.

| # | Segmento | Quién | Tiempo | Acumulado |
| --- | --- | --- | --- | --- |
| 1 | Lenguaje y tokens | P1 | 1:30 | 1:30 |
| 2 | Lexer | P2 y P5 | 3:00 | 4:30 |
| 3 | Semántico | P3 y P4 | 3:30 | 8:00 |
| 4 | Reflexión | P1 | 1:00 | 9:00 |

## 1. Lenguaje y tokens (P1, 1:30)

<!-- TODO(P1): texto. Mostrar docs/especificacion_tokens.md y docs/automata.md. -->

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

<!-- TODO(P1): versión hablada y resumida de docs/reflexion.md. -->

## Checklist de grabación

- [ ] Terminal con letra grande y fondo legible.
- [ ] Probar todos los comandos antes de grabar.
- [ ] Cronometrar cada segmento.
- [ ] Duración final < 10:00.
