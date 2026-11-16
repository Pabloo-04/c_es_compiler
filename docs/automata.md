# Autómata finito: identificadores y números

**Responsable:** Persona 1

<!-- TODO(P1): completar el diagrama y la tabla de transiciones.
     GitHub dibuja los bloques mermaid automáticamente. También se puede
     exportar como imagen a docs/img/ para el video. -->

## Identificadores

```mermaid
stateDiagram-v2
    direction LR
    [*] --> q0
    q0 --> q1: letra | _
    q1 --> q1: letra | digito | _
    q1 --> [*]: otro (aceptar ID / palabra reservada)
```

## Números

```mermaid
stateDiagram-v2
    direction LR
    [*] --> q0
    q0 --> q1: digito
    q1 --> q1: digito
    q1 --> q2: .
    q2 --> q3: digito
    q3 --> q3: digito
    q1 --> [*]: otro (aceptar NUM_ENTERO)
    q3 --> [*]: otro (aceptar NUM_REAL)
    %% TODO(P1): estados de error para 12.3.4, 3abc y "12."
```

## Tabla de transiciones

<!-- TODO(P1) -->

| Estado | letra / `_` | dígito | `.` | otro | ¿Acepta? |
| --- | --- | --- | --- | --- | --- |
| q0 | | | | | |
| q1 | | | | | |
| q2 | | | | | |
| q3 | | | | | |

## Relación con el código

Cada estado inicial corresponde a un método de `compiler/lexer.py`:
`read_identifier` y `read_number`.
