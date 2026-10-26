import pytest
from flask_jwt_extended import create_access_token

from blacklist_api import create_app
from blacklist_api.config import TestConfig
from blacklist_api.extensions import db


@pytest.fixture
def app():
    app = create_app(TestConfig)
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth(app):
    with app.app_context():
        token = create_access_token(identity="pruebas", expires_delta=False)
    return {"Authorization": f"Bearer {token}"}


UUID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"


@pytest.fixture
def agregar(client, auth):
    """POST /blacklists con un cuerpo válido; `cambios` reemplaza o agrega campos."""

    def _agregar(**cambios):
        cuerpo = {"email": "spam@ejemplo.com", "app_uuid": UUID, "blocked_reason": "Spam"}
        cuerpo.update(cambios)
        return client.post("/blacklists", json=cuerpo, headers=auth)

    return _agregar
