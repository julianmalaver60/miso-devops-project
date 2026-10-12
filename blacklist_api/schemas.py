from marshmallow import fields, pre_load, validate

from .extensions import ma
from .models import Blacklist


def normalizar_email(email):
    """Los emails se guardan y se buscan sin espacios y en minúscula."""
    return email.strip().lower()


class BlacklistInputSchema(ma.Schema):
    """Valida el cuerpo del POST /blacklists."""

    email = fields.Email(required=True)
    app_uuid = fields.UUID(required=True)
    blocked_reason = fields.String(
        load_default=None, allow_none=True, validate=validate.Length(max=255)
    )

    @pre_load
    def _normalizar(self, data, **kwargs):
        if isinstance(data, dict) and isinstance(data.get("email"), str):
            data = {**data, "email": normalizar_email(data["email"])}
        return data


class BlacklistSchema(ma.SQLAlchemyAutoSchema):
    """Serializa un registro guardado para las respuestas."""

    class Meta:
        model = Blacklist
