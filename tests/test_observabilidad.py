"""Reporte a New Relic de los 400, 404 y 409 (blacklist_api/observabilidad.py).

El agente real no se usa aquí (no se instala en Windows y en las pruebas no hay transacción):
se reemplaza por un doble que anota cada llamada a notice_error.
"""

import sys

import pytest
from flask_jwt_extended import create_access_token

from blacklist_api import create_app, observabilidad
from blacklist_api.config import TestConfig
from blacklist_api.extensions import db
from conftest import UUID


class AgenteFalso:
    def __init__(self):
        self.errores = []

    def notice_error(self, status_code=None, ignore=None):
        tipo = sys.exc_info()[0]
        self.errores.append((status_code, tipo.__name__, ignore))


@pytest.fixture
def agente(monkeypatch):
    falso = AgenteFalso()
    monkeypatch.setattr(observabilidad, "newrelic_agent", falso)
    return falso


@pytest.fixture
def cliente(agente):
    app = create_app(TestConfig)
    with app.app_context():
        token = create_access_token(identity="pruebas", expires_delta=False)
    yield app.test_client(), {"Authorization": f"Bearer {token}"}
    with app.app_context():
        db.drop_all()


def test_reporta_400_404_y_409_como_errores(cliente, agente):
    client, auth = cliente
    cuerpo = {"email": "spam@ejemplo.com", "app_uuid": UUID}

    assert client.post("/blacklists", json=cuerpo, headers=auth).status_code == 201
    assert client.post("/blacklists", json={"email": "malo"}, headers=auth).status_code == 400
    assert client.get("/no-existe").status_code == 404
    assert client.post("/blacklists", json=cuerpo, headers=auth).status_code == 409

    assert agente.errores == [
        (400, "SolicitudInvalida", False),
        (404, "RutaNoEncontrada", False),
        (409, "EmailDuplicado", False),
    ]


def test_no_reporta_exitos_ni_401(cliente, agente):
    """El 401 ya lo registra el agente por la excepción de Flask-JWT-Extended."""
    client, auth = cliente

    assert client.get("/health").status_code == 200
    assert client.get("/blacklists/spam@ejemplo.com", headers=auth).status_code == 200
    assert client.get("/blacklists/spam@ejemplo.com").status_code == 401

    assert agente.errores == []
