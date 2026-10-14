"""Microservicio de lista negra global de emails.

`create_app` arma la aplicación Flask: configuración, extensiones, rutas y tablas.
"""

import sqlalchemy as sa
from flask import Flask
from flask_restful import Api
from sqlalchemy.exc import DBAPIError

from .config import Config
from .extensions import db, jwt, ma
from .resources import BlacklistCollection, BlacklistItem, Health

# Subir este número en cada versión que se despliegue: /health lo muestra y así se ve
# qué instancias ya tienen la versión nueva durante una estrategia de despliegue.
__version__ = "1.0.4" # Lo cambie a 1.0.1 para que se vea el cambio en /health


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config["APP_VERSION"] = __version__

    if not app.config.get("JWT_SECRET_KEY"):
        raise RuntimeError(
            "Falta la variable de entorno JWT_SECRET_KEY (ver .env.example)."
        )

    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    _registrar_errores_jwt()

    api = Api(app)
    api.add_resource(Health, "/health")
    api.add_resource(BlacklistCollection, "/blacklists")
    api.add_resource(BlacklistItem, "/blacklists/<string:email>")

    with app.app_context():
        crear_tablas()

    from .cli import registrar_comandos

    registrar_comandos(app)
    return app


def crear_tablas():
    """Crea la tabla si no existe (sin migraciones: suficiente para esta entrega).

    Varios procesos de Gunicorn o varias instancias de Beanstalk pueden arrancar a la vez
    contra la misma base; si otro la creó primero, `create_all` falla y no es un error.
    """
    try:
        db.create_all()
    except DBAPIError:
        db.session.rollback()
        if not sa.inspect(db.engine).has_table("blacklists"):
            raise


def _registrar_errores_jwt():
    """Responde 401 en JSON cuando el token falta o no es válido."""

    @jwt.unauthorized_loader
    def _sin_token(motivo):
        return {"msg": "Falta el token de autorización (Bearer).", "detalle": motivo}, 401

    @jwt.invalid_token_loader
    def _token_invalido(motivo):
        return {"msg": "Token de autorización inválido.", "detalle": motivo}, 401
