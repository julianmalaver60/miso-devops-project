"""Configuración leída de variables de entorno.

Base de datos, en orden de prioridad:
1. Variables RDS_* que Elastic Beanstalk inyecta cuando la base RDS está asociada al ambiente.
2. DATABASE_URL (útil para una RDS creada aparte o un PostgreSQL local).
3. SQLite local, solo para desarrollo.
"""

import os
from urllib.parse import quote_plus


def _database_uri():
    if os.environ.get("RDS_HOSTNAME"):
        return "postgresql://{user}:{password}@{host}:{port}/{name}".format(
            user=quote_plus(os.environ["RDS_USERNAME"]),
            password=quote_plus(os.environ["RDS_PASSWORD"]),
            host=os.environ["RDS_HOSTNAME"],
            port=os.environ.get("RDS_PORT", "5432"),
            name=os.environ["RDS_DB_NAME"],
        )
    return os.environ.get("DATABASE_URL", "sqlite:///blacklist.db")


class Config:
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    # Flask-RESTful captura las excepciones; sin esto, los errores de JWT salen como 500.
    PROPAGATE_EXCEPTIONS = True


class TestConfig(Config):
    TESTING = True
    # SQLite en memoria por defecto; TEST_DATABASE_URL permite correrlas contra PostgreSQL.
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite://")
    JWT_SECRET_KEY = "clave-solo-para-pruebas-no-usar-en-aws"
