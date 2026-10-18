
# Configuración en AWS

Este documento registra los principales valores utilizados para desplegar la API del proyecto en AWS.

## Configuración general

| Parámetro | Valor |
|---|---|
| Región | `us-east-1` |
| Región AWS | N. Virginia |
| Arquitectura | RDS PostgreSQL + Elastic Beanstalk |
| VPC | `vpc-02dea8dca0fb53125` |
| Tipo de ambiente | Load Balanced |
| Acceso a la aplicación | Público mediante Application Load Balancer |
| Acceso a PostgreSQL | Privado |

## Amazon RDS

| Parámetro | Valor utilizado |
|---|---|
| Servicio | Amazon RDS |
| Motor | PostgreSQL |
| Versión | PostgreSQL 17 |
| Identificador de instancia | `database-1` |
| Nombre de base de datos | `blacklist` |
| Usuario maestro | `postgres` |
| Puerto | `5432` |
| Clase de instancia | `db.t3.micro` |
| Tipo de despliegue | Single-AZ |
| Almacenamiento | `20 GiB` |
| Tipo de almacenamiento | `gp3` |
| Storage autoscaling | Deshabilitado |
| VPC | `vpc-02dea8dca0fb53125` |
| DB Subnet Group | Default VPC subnet group |
| Publicly accessible | No |
| RDS Proxy | No |
| Authentication | Password authentication |
| Automated backups | Deshabilitados para el ambiente temporal |
| Deletion protection | Deshabilitado |
| Enhanced Monitoring | Deshabilitado |
| Database Insights | Standard |
| DevOps Guru | Deshabilitado |
| Security Group | `blacklist-rds-sg` |
| Security Group ID | `sg-088ea20a07a7dcd60` |

### Endpoint actual de RDS

```text
database-1.cqpqamiuedzv.us-east-1.rds.amazonaws.com
```

### Regla de entrada de RDS

| Tipo | Protocolo | Puerto | Origen |
|---|---|---:|---|
| PostgreSQL | TCP | `5432` | Security Group de las instancias EC2 de Elastic Beanstalk |

Durante este despliegue, el Security Group utilizado por las instancias de Beanstalk fue:

```text
sg-07289a380c456abdc
```

La regla de entrada de RDS quedó:

```text
TCP 5432
Source: sg-07289a380c456abdc
```

No se requiere acceso público a PostgreSQL.

## Elastic Beanstalk

| Parámetro | Valor utilizado |
|---|---|
| Servicio | AWS Elastic Beanstalk |
| Application name | `miso-devops-project` |
| Environment name | `Miso-devops-project-env` |
| Environment type | Web server environment |
| Environment mode | Load balanced |
| Región | `us-east-1` |
| Plataforma | Python 3.12 |
| Sistema operativo | 64bit Amazon Linux 2023 |
| Platform branch | Python 3.12 running on 64bit Amazon Linux 2023 |
| Platform version observada | `4.13.10` |
| Arquitectura EC2 | `x86_64` |
| Tipo de instancia | `t3.micro` |
| Capacidad mínima | `3` |
| Capacidad máxima | `6` |
| Balanceador | Application Load Balancer |
| Load Balancer visibility | Public |
| Listener | HTTP |
| Listener port | `80` |
| Health reporting | Enhanced |
| Managed platform updates | Deshabilitados |
| Deployment policy inicial | All at once |

## Networking de Elastic Beanstalk

| Parámetro | Valor |
|---|---|
| VPC | `vpc-02dea8dca0fb53125` |
| Instance public IP | Habilitada |
| Load Balancer | Público |
| IP address type | IPv4 |
| EC2 Security Group | `sg-07289a380c456abdc` |
| Load Balancer Security Group | `sg-03ff038c7b151934a` |

Las instancias fueron distribuidas entre varias subnets de la VPC para permitir que Elastic Beanstalk y el Application Load Balancer trabajaran en múltiples Availability Zones.

## Security Groups

### Security Group de RDS

```text
Name: blacklist-rds-sg
ID: sg-088ea20a07a7dcd60
VPC: vpc-02dea8dca0fb53125
```

Regla principal:

| Direction | Type | Protocol | Port | Source |
|---|---|---|---:|---|
| Inbound | PostgreSQL | TCP | `5432` | `sg-07289a380c456abdc` |

### Security Group de las instancias Elastic Beanstalk

```text
sg-07289a380c456abdc
```

Este grupo es creado y administrado por el stack de Elastic Beanstalk.

Su función es controlar el tráfico recibido por las instancias EC2 que ejecutan Gunicorn y la aplicación Flask.

### Security Group del Application Load Balancer

```text
sg-03ff038c7b151934a
```

Este Security Group pertenece al Application Load Balancer creado automáticamente por Elastic Beanstalk.

## Auto Scaling

| Parámetro | Valor |
|---|---:|
| Minimum instances | `3` |
| Maximum instances | `6` |
| Instance type | `t3.micro` |
| Architecture | `x86_64` |

Elastic Beanstalk administra automáticamente el Auto Scaling Group y mantiene el número de instancias dentro de este rango.

La configuración de tres instancias mínimas permite observar el comportamiento de las estrategias de despliegue solicitadas para la entrega.

## Application Load Balancer

| Parámetro | Valor |
|---|---|
| Tipo | Application Load Balancer |
| Visibility | Public |
| IP type | IPv4 |
| Listener | HTTP |
| Listener port | `80` |
| Target | Instancias EC2 de Elastic Beanstalk |
| Health Check | `/health` |

## Health Check

| Parámetro | Valor |
|---|---|
| Protocol | HTTP |
| Port | `80` |
| Path | `/health` |
| Success code | `200` |
| Interval | `15 seconds` |
| Timeout | `5 seconds` |
| Healthy threshold | `3` |
| Unhealthy threshold | `5` |
| Deregistration delay | `20 seconds` |

Respuesta esperada:

```json
{
  "status": "ok",
  "version": "1.0.0",
  "host": "<ec2-hostname>"
}
```

## Variables de entorno

| Variable | Valor/configuración |
|---|---|
| `RDS_HOSTNAME` | Endpoint actual de RDS |
| `RDS_PORT` | `5432` |
| `RDS_DB_NAME` | `blacklist` |
| `RDS_USERNAME` | `postgres` |
| `RDS_PASSWORD` | Valor privado |
| `JWT_SECRET_KEY` | Valor privado |

Los valores de `RDS_PASSWORD` y `JWT_SECRET_KEY` no deben quedar documentados ni almacenados en Git.

## Flujo de red

```text
Internet
   |
   v
Application Load Balancer
   |
   | HTTP :80
   v
Elastic Beanstalk
EC2 instances
   |
   | PostgreSQL TCP :5432
   v
Amazon RDS
PostgreSQL
```

La base de datos no recibe tráfico directamente desde Internet.

El Security Group de RDS únicamente autoriza conexiones provenientes del Security Group de las instancias EC2 de Elastic Beanstalk.

## Estrategias de despliegue

El ambiente fue dimensionado con mínimo tres instancias y máximo seis para ejecutar las cuatro estrategias solicitadas:

| Estrategia | Comportamiento esperado |
|---|---|
| All at once | Actualiza todas las instancias simultáneamente |
| Rolling | Actualiza las instancias por lotes |
| Rolling with additional batch | Agrega capacidad temporal antes de actualizar cada lote |
| Immutable | Crea un nuevo conjunto de instancias y reemplaza el anterior después de validar el despliegue |

No es necesario reconstruir el ambiente entre estrategias. Elastic Beanstalk administra cada actualización de acuerdo con la política seleccionada.