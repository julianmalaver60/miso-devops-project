UUID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"


def agregar(client, auth, **cambios):
    cuerpo = {"email": "spam@ejemplo.com", "app_uuid": UUID, "blocked_reason": "Spam"}
    cuerpo.update(cambios)
    return client.post("/blacklists", json=cuerpo, headers=auth)


def test_health_no_requiere_token(client):
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_json()
    assert cuerpo["status"] == "ok"
    assert cuerpo["version"]
    assert cuerpo["host"]


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


def test_post_email_duplicado_responde_409(client, auth):
    assert agregar(client, auth).status_code == 201
    assert agregar(client, auth, email="  SPAM@Ejemplo.com ").status_code == 409


def test_post_valida_campos(client, auth):
    casos = [
        {"email": "no-es-un-email"},
        {"app_uuid": "no-es-uuid"},
        {"blocked_reason": "x" * 256},
    ]
    for cambio in casos:
        respuesta = agregar(client, auth, **cambio)
        assert respuesta.status_code == 400, cambio
        assert list(cambio)[0] in respuesta.get_json()["errores"]


def test_post_campos_obligatorios(client, auth):
    respuesta = client.post("/blacklists", json={}, headers=auth)
    assert respuesta.status_code == 400
    assert set(respuesta.get_json()["errores"]) == {"email", "app_uuid"}


def test_post_cuerpo_no_json(client, auth):
    respuesta = client.post("/blacklists", data="hola", headers=auth)
    assert respuesta.status_code == 400


def test_get_email_en_lista(client, auth):
    agregar(client, auth)
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


def test_endpoints_exigen_token(client):
    assert client.post("/blacklists", json={}).status_code == 401
    assert client.get("/blacklists/a@b.com").status_code == 401


def test_token_invalido_responde_401(client):
    malo = {"Authorization": "Bearer esto.no.sirve"}
    assert client.get("/blacklists/a@b.com", headers=malo).status_code == 401


def test_crear_tablas_tolera_que_otro_proceso_la_cree(app, monkeypatch):
    """Simula dos instancias arrancando a la vez: create_all falla porque la tabla ya existe."""
    from sqlalchemy.exc import OperationalError

    from blacklist_api import crear_tablas
    from blacklist_api.extensions import db

    def create_all_en_carrera():
        raise OperationalError("CREATE TABLE blacklists", {}, Exception("already exists"))

    with app.app_context():
        monkeypatch.setattr(db, "create_all", create_all_en_carrera)
        crear_tablas()  # No debe lanzar: la tabla ya existe.
