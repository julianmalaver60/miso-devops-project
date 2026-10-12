# API — Lista negra global de emails

Todas las respuestas son `application/json`. Los endpoints de `/blacklists` exigen:

```
Authorization: Bearer <token>
```

Los emails se guardan y se consultan **sin espacios y en minúscula**: `Spam@Ejemplo.com` y
`spam@ejemplo.com` son el mismo.

## `POST /blacklists` — agregar un email

### Cuerpo

| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `email` | string | Sí | Email válido |
| `app_uuid` | string | Sí | UUID de la aplicación cliente |
| `blocked_reason` | string | No | Máximo 255 caracteres |

Internamente se guardan además la **IP de origen** (primera IP de `X-Forwarded-For`, o la de
la conexión si no hay proxy) y la **fecha/hora UTC** de la solicitud.

### Ejemplo

```http
POST /blacklists
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "spam@ejemplo.com",
  "app_uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "blocked_reason": "Envío masivo no autorizado"
}
```

`201 Created`

```json
{
  "msg": "El email spam@ejemplo.com fue agregado a la lista negra global.",
  "blacklist": {
    "id": 1,
    "email": "spam@ejemplo.com",
    "app_uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "blocked_reason": "Envío masivo no autorizado",
    "request_ip": "203.0.113.7",
    "created_at": "2026-10-12T16:10:02.911200+00:00"
  }
}
```

### Respuestas

| Código | Cuándo |
|---|---|
| `201` | Email agregado |
| `400` | Cuerpo no es JSON, falta un campo obligatorio o un campo no cumple su regla. `errores` dice cuál |
| `401` | Falta el token o no es válido |
| `409` | El email ya estaba en la lista |

Ejemplo de `400`:

```json
{
  "msg": "Datos inválidos.",
  "errores": {"app_uuid": ["Not a valid UUID."]}
}
```

## `GET /blacklists/<email>` — consultar un email

### Ejemplo

```http
GET /blacklists/spam@ejemplo.com
Authorization: Bearer <token>
```

`200 OK` — está en la lista:

```json
{"email": "spam@ejemplo.com", "is_blacklisted": true, "blocked_reason": "Envío masivo no autorizado"}
```

`200 OK` — no está:

```json
{"email": "limpio@ejemplo.com", "is_blacklisted": false, "blocked_reason": null}
```

| Código | Cuándo |
|---|---|
| `200` | Siempre que el token sea válido; `is_blacklisted` dice si está o no |
| `401` | Falta el token o no es válido |

## `GET /health` — health check

Sin token. No consulta la base, para que el balanceador no marque instancias como caídas por
una demora de RDS. Devuelve la versión desplegada y el nombre de la instancia que respondió,
útil para seguir una estrategia de despliegue.

```json
{"status": "ok", "version": "1.0.0", "host": "ip-172-31-5-10.ec2.internal"}
```

## Decisiones de diseño

- **Un email aparece una sola vez** en la lista (restricción `UNIQUE`). Agregarlo de nuevo
  responde `409` en vez de duplicar el registro, así el `GET` siempre tiene un único motivo.
- **Token estático firmado (JWT)**: el enunciado permite un token predefinido y pide
  Flask-JWT-Extended en el stack. Se genera una vez con `flask --app application
  generar-token` y no vence; deja de servir si cambia `JWT_SECRET_KEY`.
- **Sin migraciones**: la tabla se crea con `db.create_all()` al arrancar. Basta para esta
  entrega; si el modelo cambia, hay que recrear la tabla o agregar Flask-Migrate. Si varias
  instancias arrancan a la vez y otra ya creó la tabla, el error se ignora (probado con 4
  procesos de Gunicorn contra PostgreSQL).
- **Controlador `psycopg` (v3), no `psycopg2`**: SQLAlchemy 2.1 usa `psycopg` por defecto para
  las URL `postgresql://`. Con `psycopg2` la app falla al conectarse.
- **La IP registrada se puede falsear** enviando `X-Forwarded-For`; es un dato de auditoría,
  no un control de seguridad.
