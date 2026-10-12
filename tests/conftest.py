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
