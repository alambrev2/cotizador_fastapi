"""Flujo de magic link y transiciones de estado usando una BD temporal."""
import secrets
from datetime import timedelta
from decimal import Decimal

from sqlmodel import select

from app.core.timeutils import utcnow
from app.models import User, Quote, RoleEnum, QuoteEstado


def test_magic_link_and_status(db):
    user = User(
        username="clientetesto",
        email="clientetesto@test.com",
        role=RoleEnum.Cliente,
        hashed_password="fakehashpassword",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = secrets.token_urlsafe(32)
    user.magic_token = token
    user.magic_token_expires = utcnow() + timedelta(days=30)
    db.add(user)
    db.commit()
    db.refresh(user)
    assert user.magic_token == token

    quote = Quote(
        cliente_id=user.cliente_id,
        estado=QuoteEstado.Enviada.value,
        total=Decimal("150.00"),
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)

    quote.estado = QuoteEstado.Aprobacion_Solicitada.value
    db.add(quote)
    db.commit()
    db.refresh(quote)
    assert quote.estado == QuoteEstado.Aprobacion_Solicitada.value
