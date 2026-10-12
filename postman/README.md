# Postman

Responsable: **David**. Aquí van la colección y el environment exportados en JSON (requisito
del enunciado), más la URL de la documentación publicada.

## Archivos

| Archivo | Contenido |
|---|---|
| `blacklist-api.postman_collection.json` | Colección con los escenarios de prueba |
| `blacklist-aws.postman_environment.json` | Environment con `base_url` y `token` |

Documentación publicada: *(pegar la URL aquí y en el documento de la entrega)*

## Variables del environment

| Variable | Valor inicial (el que se exporta) | Valor actual (solo local) |
|---|---|---|
| `base_url` | `http://<url-del-ambiente>` | igual |
| `token` | **vacío** | el token real |

El repo es público: **el token real nunca va en el valor inicial**. Revisar el JSON antes de
subirlo.

Autorización de la colección: *Bearer Token* = `{{token}}`, heredada por todas las solicitudes.

## Escenarios sugeridos

Son los mismos casos que cubren las pruebas automáticas (`tests/test_blacklists.py`); ver
[`docs/api.md`](../docs/api.md) para cuerpos y respuestas.

| # | Solicitud | Esperado |
|---|---|---|
| 1 | `GET /health` sin token | 200 |
| 2 | `POST /blacklists` completo | 201 |
| 3 | `POST /blacklists` sin `blocked_reason` | 201 |
| 4 | `POST /blacklists` con un email ya agregado | 409 |
| 5 | `POST /blacklists` con email inválido | 400 |
| 6 | `POST /blacklists` con `app_uuid` inválido | 400 |
| 7 | `POST /blacklists` con `blocked_reason` de 256+ caracteres | 400 |
| 8 | `POST /blacklists` sin token | 401 |
| 9 | `GET /blacklists/<email agregado>` | 200, `is_blacklisted: true` y motivo |
| 10 | `GET /blacklists/<email nuevo>` | 200, `is_blacklisted: false` |
| 11 | `GET /blacklists/<email>` sin token | 401 |

Para que los escenarios se puedan repetir, usar un email distinto por corrida en el 2, p. ej.
`prueba-{{$timestamp}}@ejemplo.com`, guardándolo en una variable para el 4 y el 9.
