"""POST /blacklists: agregar un email a la lista negra global."""

from conftest import UUID


def test_post_agrega_email_y_guarda_ip_y_fecha(client, auth):
    respuesta = client.post(
        "/blacklists",
        json={"email": "spam@ejemplo.com", "app_uuid": UUID, "blocked_reason": "Spam"},
        headers={**auth, "X-Forwarded-For": "203.0.113.7, 10.0.0.1"},
    )
    assert respuesta.status_code == 201
    registro = respuesta.get_json()["blacklist"]
    assert registro["email"] == "spam@ejemplo.com"
    assert registro["app_uuid"] == UUID
    assert registro["request_ip"] == "203.0.113.7"
    assert registro["created_at"]


def test_post_sin_motivo_es_valido(client, auth):
    respuesta = client.post(
        "/blacklists", json={"email": "otro@ejemplo.com", "app_uuid": UUID}, headers=auth
    )
    assert respuesta.status_code == 201
    assert respuesta.get_json()["blacklist"]["blocked_reason"] is None


def test_post_email_duplicado_responde_409(agregar):
    assert agregar().status_code == 201
    assert agregar(email="  SPAM@Ejemplo.com ").status_code == 409


def test_post_valida_campos(agregar):
    casos = [
        {"email": "no-es-un-email"},
        {"app_uuid": "no-es-uuid"},
        {"blocked_reason": "x" * 256},
    ]
    for cambio in casos:
        respuesta = agregar(**cambio)
        assert respuesta.status_code == 400, cambio
        assert list(cambio)[0] in respuesta.get_json()["errores"]


def test_post_campos_obligatorios(client, auth):
    respuesta = client.post("/blacklists", json={}, headers=auth)
    assert respuesta.status_code == 400
    assert set(respuesta.get_json()["errores"]) == {"email", "app_uuid"}


def test_post_cuerpo_no_json(client, auth):
    respuesta = client.post("/blacklists", data="hola", headers=auth)
    assert respuesta.status_code == 400


def test_post_sin_token_responde_401(client):
    assert client.post("/blacklists", json={}).status_code == 401
