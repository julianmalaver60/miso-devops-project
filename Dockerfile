# Imagen del microservicio para AWS Fargate (Entrega 3).
#
# Base desde ECR Public (espejo oficial de las imágenes de Docker Hub): CodeBuild descarga
# sin el límite de pulls anónimos de Docker Hub, que comparte IP con otros clientes.
FROM public.ecr.aws/docker/library/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias primero: si solo cambia el código, Docker reutiliza esta capa.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY application.py .
COPY blacklist_api/ blacklist_api/

# Usuario sin privilegios. instance/ es donde Flask guarda el SQLite local cuando no hay
# base configurada (solo pruebas locales; en AWS la base es RDS).
RUN useradd --create-home --uid 1000 app \
    && mkdir -p instance && chown app:app instance
USER app

EXPOSE 5000

# 2 workers alcanzan para 0,5 vCPU de Fargate. Los logs van a stdout (CloudWatch).
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "application:application"]
