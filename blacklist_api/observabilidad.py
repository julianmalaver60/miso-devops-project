"""Reporte a New Relic de los errores de cliente que la API responde sin lanzar excepción.

El agente de Python solo registra como error las excepciones. El 401 ya llega así (Flask-JWT-
Extended lanza una excepción cuando falta el token o no es válido), pero el 400, el 404 y el 409
son respuestas normales y no aparecerían en Errors Inbox. Además, el agente ignora el 404 por
defecto (`error_collector.ignore_status_codes`). Este módulo los reporta con una excepción por
código, para que cada uno forme su propio grupo en Errors Inbox.

Sin el agente (Windows, pruebas) o fuera de una transacción de New Relic no hace nada.
"""

from flask import request

try:
    import newrelic.agent as newrelic_agent
except ImportError:  # el agente no se instala en Windows (ver requirements.txt)
    newrelic_agent = None


class SolicitudInvalida(Exception):
    """400: el cuerpo no es JSON o no pasa la validación."""


class RutaNoEncontrada(Exception):
    """404: la ruta no existe."""


class EmailDuplicado(Exception):
    """409: el email ya está en la lista negra."""


ERRORES_POR_CODIGO = {400: SolicitudInvalida, 404: RutaNoEncontrada, 409: EmailDuplicado}


def registrar_reporte_de_errores(app):
    if newrelic_agent is None:
        return

    @app.after_request
    def _reportar(respuesta):
        clase = ERRORES_POR_CODIGO.get(respuesta.status_code)
        if clase:
            # Sin el email en el mensaje: no se manda información personal a New Relic.
            mensaje = f"HTTP {respuesta.status_code} en {request.method} {request.url_rule or request.path}"
            try:
                raise clase(mensaje)
            except clase:
                # ignore=False: se registra aunque el código esté en la lista de ignorados (404).
                newrelic_agent.notice_error(status_code=respuesta.status_code, ignore=False)
        return respuesta
