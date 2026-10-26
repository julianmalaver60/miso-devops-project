"""GET /health: health check de Elastic Beanstalk."""


def test_health_no_requiere_token(client):
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_json()
    assert cuerpo["status"] == "ok"
    assert cuerpo["version"]
    assert cuerpo["host"]
