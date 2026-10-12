# Despliegue en AWS (RDS + Elastic Beanstalk)

Responsable: **Julián**. Esta guía es el punto de partida; quien despliegue debe ajustarla con
lo que realmente hizo (y las capturas van al documento PDF de la entrega, ítem 1).

> Lo marcado *(verificado)* se comprobó en la documentación de AWS o en pruebas locales el
> 2026-10-12. El resto es la configuración recomendada: confirmar en la consola.

## Antes de empezar

- Cuenta del grupo, región **us-east-1 (N. Virginia)**. Entrar con el usuario IAM propio, no root.
- Los recursos cuestan dinero desde que se crean (cuenta de pago, sin créditos). Ver
  [Al terminar](#al-terminar).

## 1. Base de datos (RDS PostgreSQL)

**Crearla aparte, no desde el asistente de Beanstalk.** Si la RDS se crea dentro del ambiente,
al terminar el ambiente se borra la base; separada, el ambiente se puede recrear sin perder datos.

| Opción | Valor recomendado |
|---|---|
| Motor | PostgreSQL 17 (probado localmente con 17 *(verificado)*) |
| Plantilla | *Free tier* / *Dev/Test* |
| Clase | `db.t4g.micro` o `db.t3.micro` |
| Almacenamiento | 20 GB gp3, sin autoescalado |
| Disponibilidad | Single-AZ |
| Nombre de la base inicial | `blacklist` |
| Acceso público | No |
| Grupo de seguridad | Permitir 5432 **solo** desde el grupo de seguridad de las instancias de Beanstalk |

Guardar el endpoint, usuario y contraseña: van como variables de entorno en Beanstalk, **nunca
en el repo**.

## 2. Paquete de la aplicación

Desde la raíz del repo, con los cambios ya en un commit:

```bash
git archive -o blacklist-v1.0.0.zip HEAD
```

El `.zip` lleva el código en la raíz (no dentro de una carpeta), que es lo que Beanstalk
espera. Sale sin `.venv/`, `.env` ni `instance/`.

## 3. Ambiente de Elastic Beanstalk

| Opción | Valor |
|---|---|
| Tipo | *Web server environment* |
| Plataforma | **Python 3.12 running on 64bit Amazon Linux 2023** *(verificado: plataforma soportada)* |
| Código | Subir el `.zip` del paso 2 |
| Tipo de ambiente | *Load balanced* (las estrategias de despliegue necesitan varias instancias) |
| Capacidad | Mín. **3**, máx. **6** instancias (recomendación del enunciado) |
| Tipo de instancia | `t3.micro` |
| Balanceador | Application Load Balancer |

No hace falta `Procfile`: Beanstalk usa Gunicorn y busca el objeto `application` en
`application.py` *(verificado)*.

### Variables de entorno

*Configuration → Updates, monitoring, and logging → Environment properties*:

| Variable | Valor |
|---|---|
| `JWT_SECRET_KEY` | Cadena aleatoria de 32+ caracteres: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `RDS_HOSTNAME` | Endpoint de la RDS |
| `RDS_PORT` | `5432` |
| `RDS_DB_NAME` | `blacklist` |
| `RDS_USERNAME` | Usuario maestro de la RDS |
| `RDS_PASSWORD` | Contraseña de la RDS |

La app crea la tabla sola al arrancar, y tolera que varias instancias arranquen a la vez
*(verificado con 4 procesos de Gunicorn contra PostgreSQL)*.

### Health check

*Configuration → Load balancer → Processes → default*: **Health check path = `/health`**.

`/health` no pide token ni consulta la base, y responde la versión y el host de la instancia:

```json
{"status": "ok", "version": "1.0.0", "host": "ip-172-31-5-10.ec2.internal"}
```

## 4. Verificar

```bash
curl http://<url-del-ambiente>/health
```

Luego, con Postman (colección en [`postman/`](../postman/)), el POST y el GET con el token.

### Generar el token para Postman

El token debe firmarse con **la misma** `JWT_SECRET_KEY` que tiene Beanstalk:

```bash
JWT_SECRET_KEY='<la de Beanstalk>' flask --app application generar-token
```

Pasárselo a David por privado. No va en el repo.

## Capturas para el documento (ítem 1, 10 %)

- [ ] a. Configuración de la RDS (motor, clase, red, grupo de seguridad).
- [ ] b. Configuración del ambiente de Beanstalk (plataforma, capacidad, variables sin mostrar valores secretos).
- [ ] c. Configuración del health check (`/health`) y el ambiente en estado *Ok*.

## Al terminar

Cuando no se esté usando por días, o al terminar la entrega **después de la calificación**:

- [ ] Beanstalk → *Actions* → **Terminate environment**.
- [ ] RDS → **Delete** (decidir si con snapshot).
- [ ] EC2: confirmar que no quedan instancias, balanceadores, volúmenes ni IPs elásticas.
