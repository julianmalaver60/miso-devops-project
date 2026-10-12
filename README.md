# miso-devops-project

Microservicio de **lista negra global de emails** — proyecto del curso *DevOps: Agilizando el
Despliegue Continuo de Aplicaciones* (MISO, Universidad de los Andes, 2026-15). Equipo
**GPT Abusers**.

Permite que los sistemas internos de una compañía **agreguen** un email a la lista negra
global y **consulten** si un email está en ella. Se despliega en **AWS Elastic Beanstalk** con
**PostgreSQL en AWS RDS**.

| Entrega | Tema | Estado |
|---|---|---|
| 1 | Despliegue manual en Beanstalk (sin CI/CD) | En curso |

## Equipo y responsabilidades (Entrega 1)

| Integrante | Parte | Guía |
|---|---|---|
| Ricardo Moreno | API en Flask | este README y [`docs/api.md`](docs/api.md) |
| Julián Malaver | RDS, Elastic Beanstalk y health checks | [`docs/despliegue.md`](docs/despliegue.md) |
| David Indaburu | Colección y documentación en Postman | [`postman/README.md`](postman/README.md) |
| María José | Estrategias de despliegue y documento | [`docs/estrategias-despliegue.md`](docs/estrategias-despliegue.md) |

## Endpoints

Ambos requieren el encabezado `Authorization: Bearer <token>`. Detalle, ejemplos y códigos
de respuesta en [`docs/api.md`](docs/api.md).

| Método | Ruta | Qué hace |
|---|---|---|
| `POST` | `/blacklists` | Agrega un email (`email`, `app_uuid`, `blocked_reason` opcional) |
| `GET` | `/blacklists/<email>` | Dice si el email está en la lista y por qué |
| `GET` | `/health` | Health check para Beanstalk (sin token); muestra versión e instancia |

## Stack

Python 3.12 · Flask · Flask-SQLAlchemy · Flask-RESTful · Flask-Marshmallow ·
Flask-JWT-Extended · Werkzeug · PostgreSQL (controlador `psycopg` 3). Versiones fijadas en
`requirements.txt`.

## Estructura

```
application.py          Punto de entrada WSGI (Beanstalk busca `application` aquí)
blacklist_api/
  __init__.py           create_app, versión de la app y creación de tablas
  config.py             Variables de entorno y conexión a la base
  extensions.py         db, ma, jwt
  models.py             Tabla `blacklists`
  schemas.py            Validación de entrada y serialización (Marshmallow)
  resources.py          Endpoints (Flask-RESTful)
  cli.py                Comando `generar-token`
tests/                  Pruebas con pytest (SQLite en memoria o PostgreSQL)
docs/
  api.md                Contrato del API con ejemplos
  despliegue.md         RDS + Beanstalk paso a paso
  estrategias-despliegue.md  Cómo ejecutar y documentar las 4 estrategias
postman/                Colección y environment de Postman exportados
.github/                Plantilla de pull request
requirements.txt        Dependencias de producción (las instala Beanstalk)
requirements-dev.txt    Producción + herramientas de prueba
.env.example            Variables de entorno de ejemplo
```

## Correr en local

Requiere Python 3.12. Comandos para Git Bash; en PowerShell el venv se activa con
`.venv\Scripts\Activate.ps1`.

```bash
python -m venv .venv
source .venv/Scripts/activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env                 # y poner un JWT_SECRET_KEY de 32+ caracteres
flask --app application run          # http://127.0.0.1:5000
```

Sin `DATABASE_URL`, la app usa SQLite en `instance/blacklist.db`. La tabla se crea sola al
arrancar.

### Token Bearer

El enunciado permite un token estático. Se genera una vez, sin vencimiento, firmado con
`JWT_SECRET_KEY`:

```bash
flask --app application generar-token
```

El token solo es válido contra un servidor que tenga **la misma** `JWT_SECRET_KEY`. Para AWS,
generarlo con la clave configurada en Beanstalk y guardarlo en el environment de Postman.

### Pruebas

```bash
pytest
```

Por defecto usan SQLite en memoria. Para correrlas contra PostgreSQL real (lo que usa RDS),
con Docker:

```bash
docker run -d --rm --name pg-pruebas -e POSTGRES_PASSWORD=pruebas -e POSTGRES_DB=blacklist -p 55432:5432 postgres:17
TEST_DATABASE_URL=postgresql://postgres:pruebas@localhost:55432/blacklist pytest
docker stop pg-pruebas
```

## Configuración

| Variable | Obligatoria | Uso |
|---|---|---|
| `JWT_SECRET_KEY` | Sí | Firma del token. La app no arranca sin ella |
| `RDS_HOSTNAME`, `RDS_PORT`, `RDS_DB_NAME`, `RDS_USERNAME`, `RDS_PASSWORD` | En AWS | Conexión a la RDS; se ponen como propiedades del ambiente de Beanstalk |
| `DATABASE_URL` | No | Alternativa: URL completa de PostgreSQL (`postgresql://usuario:clave@host:5432/base`) |
| `TEST_DATABASE_URL` | No | Base para `pytest`; sin ella, SQLite en memoria |

## Despliegue en Elastic Beanstalk

Paso a paso en [`docs/despliegue.md`](docs/despliegue.md). Lo esencial:

- Plataforma **Python 3.12 running on 64bit Amazon Linux 2023**; sin `Procfile` (Beanstalk
  usa Gunicorn y el objeto `application` de `application.py`).
- Health check del balanceador: **`/health`**.
- Paquete: `git archive -o blacklist-v<versión>.zip HEAD`.
- Versión de la app: `__version__` en `blacklist_api/__init__.py`; subirla en cada despliegue.

## Reglas del repositorio

- **Nunca subir secretos** (el repo es público): ni `.env`, ni credenciales de AWS, ni la
  contraseña de RDS, ni el token real. Van en variables de entorno de Beanstalk.
- Trabajo en ramas (`feature/...`) con *pull request* a `main`.
- Archivos agregados por nombre, nunca `git add .`.
- Fines de línea normalizados a LF (`.gitattributes`).
- Documentación y mensajes de commit en español.
