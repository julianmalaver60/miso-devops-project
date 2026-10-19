# Postman — Entrega 1

Responsable: **David Indaburu**. Colección con **21 escenarios**, **70 aserciones** y un ejemplo de solicitud/respuesta por escenario.

## Archivos

| Archivo | Contenido |
|---|---|
| [blacklist-api.postman_collection.json](blacklist-api.postman_collection.json) | Colección v2.1: endpoints, ejemplos, datos dinámicos y pruebas |
| [blacklist-aws.postman_environment.json](blacklist-aws.postman_environment.json) | Environment `Blacklist API — AWS`: URL del servicio y token vacío |

## Importación y autenticación

1. En Postman Desktop, usar **Import** y seleccionar ambos archivos JSON.
2. Seleccionar el environment **Blacklist API — AWS**.
3. Configurar únicamente el valor local de `token` con una referencia al JWT guardado en Postman Vault (`{{vault:nombre_del_secreto}}`). Mantener vacío su valor compartido.
4. La colección utiliza `Authorization: Bearer {{token}}`. `/health` y los escenarios sin token tienen autorización desactivada; los escenarios de JWT inválido generan su propio valor de prueba.

| Variable | Alcance | Valor exportado |
|---|---|---|
| `base_url` | Environment | `http://miso-devops-project-env.eba-j23tens3.us-east-1.elasticbeanstalk.com` |
| `token` | Environment | Vacío |
| `app_uuid`, `blocked_reason` | Colección | Datos de ejemplo |
| Emails y motivos de 255/256 caracteres | Colección | Ejemplos; los scripts generan los valores de ejecución |

El JWT real no se incluye en los JSON ni en este repositorio. Cada integrante configura su acceso local. Marcar una variable como sensible oculta su visualización, pero no reemplaza la necesidad de mantener vacío el valor compartido/exportado.

## Ejecución

Abrir la colección y seleccionar **Run → Functional → Local**:

- Environment: **Blacklist API — AWS**.
- Solicitudes: las 21, en orden del 01 al 21.
- Iteraciones: **1**. Pausa: **0 ms**. Sin archivo de datos.
- **Persist responses for a session**: activado.
- **Keep variable values**: desactivado.

Cada ejecución completa crea tres registros. Los correos usan un UUID aleatorio para permitir nuevas ejecuciones sin colisiones; las consultas y el caso duplicado reutilizan los valores creados antes en la misma corrida.

## Escenarios

| N.º | Escenario | Método | HTTP esperado |
|---|---|---|---|
| 01 | Health check sin autenticación | `GET` | 200 |
| 02 | Crear email con motivo | `POST` | 201 |
| 03 | Consultar email registrado | `GET` | 200 |
| 04 | Duplicado con mayúsculas y otra app | `POST` | 409 |
| 05 | Consultar con mayúsculas y conservar motivo | `GET` | 200 |
| 06 | Crear email sin motivo | `POST` | 201 |
| 07 | Consultar email sin motivo | `GET` | 200 |
| 08 | Crear motivo de exactamente 255 caracteres | `POST` | 201 |
| 09 | Consultar email inexistente | `GET` | 200 |
| 10 | Email inválido | `POST` | 400 |
| 11 | app_uuid inválido | `POST` | 400 |
| 12 | Motivo de 256 caracteres | `POST` | 400 |
| 13 | Falta email | `POST` | 400 |
| 14 | Falta app_uuid | `POST` | 400 |
| 15 | Faltan ambos campos obligatorios | `POST` | 400 |
| 16 | Cuerpo no JSON | `POST` | 400 |
| 17 | JSON de tipo arreglo | `POST` | 400 |
| 18 | POST sin token | `POST` | 401 |
| 19 | GET sin token | `GET` | 401 |
| 20 | POST con JWT inválido | `POST` | 401 |
| 21 | GET con JWT inválido | `GET` | 401 |

## Formato de entrega

La colección se entrega en formato **Postman Collection v2.1** y el environment en JSON. Ambos archivos se encuentran en esta carpeta. El environment contiene `base_url` y `token`; el valor exportado de `token` está vacío. Las variables de datos de prueba pertenecen a la colección.
