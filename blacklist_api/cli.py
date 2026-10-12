"""Comandos de consola: `flask --app application <comando>`."""

import click
from flask_jwt_extended import create_access_token


def registrar_comandos(app):
    @app.cli.command("generar-token")
    @click.option("--cliente", default="postman", show_default=True,
                  help="Identidad que queda dentro del token.")
    def generar_token(cliente):
        """Imprime un token Bearer sin vencimiento.

        El enunciado permite un token estático. Este token es válido mientras
        JWT_SECRET_KEY no cambie: hay que generarlo con la misma clave que tenga Beanstalk.
        """
        click.echo(create_access_token(identity=cliente, expires_delta=False))
