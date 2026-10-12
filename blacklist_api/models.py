from datetime import datetime, timezone

import sqlalchemy as sa

from .extensions import db


class Blacklist(db.Model):
    """Un email en la lista negra global. Cada email aparece una sola vez."""

    __tablename__ = "blacklists"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), nullable=False, unique=True, index=True)
    app_uuid = db.Column(sa.Uuid, nullable=False)
    blocked_reason = db.Column(db.String(255), nullable=True)
    # IPv6 ocupa hasta 45 caracteres.
    request_ip = db.Column(db.String(45), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
