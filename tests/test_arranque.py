"""Arranque de la app: creación de tablas con varios procesos a la vez."""


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
