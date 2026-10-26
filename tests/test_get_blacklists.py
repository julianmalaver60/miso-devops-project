"""GET /blacklists/<email>: consultar si un email está en la lista negra global."""


def test_get_email_en_lista(client, auth, agregar):
    agregar()
    respuesta = client.get("/blacklists/SPAM@ejemplo.com", headers=auth)
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        "email": "spam@ejemplo.com",
        "is_blacklisted": True,
        "blocked_reason": "Spam",
    }


def test_get_email_fuera_de_lista(client, auth):
    respuesta = client.get("/blacklists/limpio@ejemplo.com", headers=auth)
    assert respuesta.status_code == 200
    assert respuesta.get_json()["is_blacklisted"] is False
    assert respuesta.get_json()["blocked_reason"] is None


def test_get_sin_token_responde_401(client):
    assert client.get("/blacklists/a@b.com").status_code == 401


def test_token_invalido_responde_401(client):
    malo = {"Authorization": "Bearer esto.no.sirve"}
    assert client.get("/blacklists/a@b.com", headers=malo).status_code == 401
