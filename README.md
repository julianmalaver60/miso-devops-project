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
Dockerfile              Imagen para Fargate (Gunicorn, puerto 5000)
.dockerignore           Lo que no entra a la imagen (.env, .venv, pruebas, docs)
requirements.txt        Dependencias de producción (incluye Gunicorn)
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

Hay un archivo por endpoint, para que se vea de un vistazo qué cubre cada uno:

| Archivo | Endpoint |
|---|---|
| `tests/test_health.py` | `GET /health` |
| `tests/test_post_blacklists.py` | `POST /blacklists` |
| `tests/test_get_blacklists.py` | `GET /blacklists/<email>` |
| `tests/test_arranque.py` | Arranque de la app (creación de tablas) |

Por defecto usan SQLite en memoria, así que no necesitan un motor de base de datos: así
corren en CodeBuild. Para correrlas contra PostgreSQL real (lo que usa RDS),
con Docker:

```bash
docker run -d --rm --name pg-pruebas -e POSTGRES_PASSWORD=pruebas -e POSTGRES_DB=blacklist -p 55432:5432 postgres:17
TEST_DATABASE_URL=postgresql://postgres:pruebas@localhost:55432/blacklist pytest
docker stop pg-pruebas
```

## Cómo trabajamos

Rama `feature/...` → pull request a `main` → **cada quien fusiona su propio PR**. Con el
pipeline de CI (Entrega 2), cada commit a `main` dispara el build en CodeBuild: correr `pytest`
antes de fusionar.

## Configuración

| Variable | Obligatoria | Uso |
|---|---|---|
| `JWT_SECRET_KEY` | Sí | Firma del token. La app no arranca sin ella |
| `RDS_HOSTNAME`, `RDS_PORT`, `RDS_DB_NAME`, `RDS_USERNAME`, `RDS_PASSWORD` | En AWS | Conexión a la RDS. En Beanstalk, propiedades del ambiente; en Fargate, Parameter Store (ver «Contenedor») |
| `DATABASE_URL` | No | Alternativa: URL completa de PostgreSQL (`postgresql://usuario:clave@host:5432/base`) |
| `TEST_DATABASE_URL` | No | Base para `pytest`; sin ella, SQLite en memoria |

## Contenedor (Entrega 3, AWS Fargate)

La imagen corre Gunicorn con 2 workers en el puerto **5000**, con un usuario sin privilegios.
La imagen base sale de ECR Public (`public.ecr.aws/docker/library/python:3.12-slim`) y no de
Docker Hub, para que CodeBuild no choque con el límite de descargas anónimas de Docker Hub.

Probarla en local (Git Bash, con Docker Desktop en «Engine running»):

```bash
docker build -t blacklist-api:local .
docker run --rm -p 5000:5000 -e JWT_SECRET_KEY=<32+ caracteres> blacklist-api:local
curl localhost:5000/health
```

Sin variables `RDS_*` usa SQLite dentro del contenedor (solo para probar). Verificado el
2026-11-10 también contra PostgreSQL 17 con las variables `RDS_*`: `/health` 200, `POST` 201,
`GET` encuentra el email y responde 401 sin token.

### Secretos en Parameter Store

La definición de tarea **no lleva valores**, solo referencias. Parámetros creados en `us-east-1`
(copiados de las propiedades del ambiente de Beanstalk, así el token de Postman sigue valiendo):

| Parámetro | Tipo |
|---|---|
| `/blacklist-api/JWT_SECRET_KEY` | SecureString |
| `/blacklist-api/RDS_PASSWORD` | SecureString |
| `/blacklist-api/RDS_HOSTNAME`, `RDS_PORT`, `RDS_DB_NAME`, `RDS_USERNAME` | String |

En `taskdef.json`, dentro del contenedor:

```json
"secrets": [
  {"name": "JWT_SECRET_KEY", "valueFrom": "arn:aws:ssm:us-east-1:<cuenta>:parameter/blacklist-api/JWT_SECRET_KEY"},
  {"name": "RDS_PASSWORD",   "valueFrom": "arn:aws:ssm:us-east-1:<cuenta>:parameter/blacklist-api/RDS_PASSWORD"},
  {"name": "RDS_HOSTNAME",   "valueFrom": "arn:aws:ssm:us-east-1:<cuenta>:parameter/blacklist-api/RDS_HOSTNAME"},
  {"name": "RDS_PORT",       "valueFrom": "arn:aws:ssm:us-east-1:<cuenta>:parameter/blacklist-api/RDS_PORT"},
  {"name": "RDS_DB_NAME",    "valueFrom": "arn:aws:ssm:us-east-1:<cuenta>:parameter/blacklist-api/RDS_DB_NAME"},
  {"name": "RDS_USERNAME",   "valueFrom": "arn:aws:ssm:us-east-1:<cuenta>:parameter/blacklist-api/RDS_USERNAME"}
]
```

El **rol de ejecución** de la tarea necesita `ssm:GetParameters` sobre
`arn:aws:ssm:us-east-1:<cuenta>:parameter/blacklist-api/*`. Desde la consola o CLI:
`aws ssm get-parameters-by-path --path /blacklist-api` (en Git Bash, anteponer
`MSYS_NO_PATHCONV=1`, o convierte la ruta en una de Windows).

### Ramas de demostración (escenarios fallidos del documento)

| Rama | Cambio | Qué pasa en el pipeline |
|---|---|---|
| `demo/ci-fallido` | `blocked_reason` acepta 300 caracteres en vez de 255 (`schemas.py`) | Falla `test_post_valida_campos` en CodeBuild: no se construye imagen ni se despliega |
| `demo/cd-fallido` | Gunicorn escucha en el puerto 8000 en vez de 5000 (`Dockerfile`) | Las pruebas pasan y la imagen llega a ECR, pero el health check del ALB (puerto 5000) falla en las tareas nuevas: CodeDeploy no pasa el tráfico y hace rollback |

Uso: fusionar la rama a `main`, capturar la ejecución y revertir enseguida con un PR de
*revert*. Con la configuración `ECSAllAtOnce` y sin hook de validación, CodeDeploy espera
hasta **60 minutos** a que las tareas nuevas queden sanas antes de fallar
([documentación de AWS](https://docs.aws.amazon.com/codedeploy/latest/userguide/troubleshooting-ecs.html)).

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
