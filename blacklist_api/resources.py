import socket

from flask import current_app, request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import Blacklist
from .schemas import BlacklistInputSchema, BlacklistSchema, normalizar_email

entrada_schema = BlacklistInputSchema()
blacklist_schema = BlacklistSchema()


def obtener_ip_cliente():
    """IP de quien hace la solicitud.

    En Beanstalk la app está detrás del balanceador y de nginx, así que `remote_addr` es la
    IP del proxy; la del cliente es la primera de `X-Forwarded-For`. El cliente puede
    falsear ese encabezado: sirve como registro, no como control de seguridad.
    """
    reenviada = request.headers.get("X-Forwarded-For", "")
    ip = reenviada.split(",")[0].strip() if reenviada else request.remote_addr
    return (ip or "desconocida")[:45]


class Health(Resource):
    """Health check para Elastic Beanstalk. No requiere token ni toca la base.

    `host` identifica la instancia EC2 que respondió (p. ej. ip-172-31-5-10).
    """

    def get(self):
        return {
            "status": "ok",
            "version": current_app.config["APP_VERSION"],
            "host": socket.gethostname(),
        }, 200


class BlacklistCollection(Resource):
    method_decorators = [jwt_required()]

    def post(self):
        datos = request.get_json(silent=True)
        if not isinstance(datos, dict):
            return {"msg": "El cuerpo de la solicitud debe ser un objeto JSON."}, 400

        try:
            valido = entrada_schema.load(datos)
        except ValidationError as error:
            return {"msg": "Datos inválidos.", "errores": error.messages}, 400

        if db.session.execute(
            db.select(Blacklist.id).filter_by(email=valido["email"])
        ).first():
            return {"msg": f"El email {valido['email']} ya está en la lista negra global."}, 409

        registro = Blacklist(**valido, request_ip=obtener_ip_cliente())
        db.session.add(registro)
        try:
            db.session.commit()
        except IntegrityError:
            # Otra solicitud lo agregó entre la consulta y el commit.
            db.session.rollback()
            return {"msg": f"El email {valido['email']} ya está en la lista negra global."}, 409

        return {
            "msg": f"El email {registro.email} fue agregado a la lista negra global.",
            "blacklist": blacklist_schema.dump(registro),
        }, 201


class BlacklistItem(Resource):
    method_decorators = [jwt_required()]

    def get(self, email):
        email = normalizar_email(email)
        registro = db.session.execute(
            db.select(Blacklist).filter_by(email=email)
        ).scalar_one_or_none()

        return {
            "email": email,
            "is_blacklisted": registro is not None,
            "blocked_reason": registro.blocked_reason if registro else None,
        }, 200
