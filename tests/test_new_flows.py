from sqlmodel import Session, select
from app.database import engine
from app.models import User, Quote, RoleEnum
from datetime import datetime, timedelta
import secrets

def test_magic_link_and_status():
    with Session(engine) as db:
        # 1. Buscar o crear un usuario cliente de prueba
        user = db.exec(select(User).where(User.role == RoleEnum.Cliente)).first()
        if not user:
            print("Creando usuario cliente para prueba...")
            user = User(
                username="clientetesto",
                email="clientetesto@test.com",
                role=RoleEnum.Cliente,
                hashed_password="fakehashpassword"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # 2. Generar token
        token = secrets.token_urlsafe(32)
        user.magic_token = token
        user.magic_token_expires = datetime.utcnow() + timedelta(days=30)
        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"OK: Token generado para el usuario {user.username}: {user.magic_token}")

        # 3. Buscar o crear una cotización
        quote = db.exec(select(Quote).where(Quote.cliente_id == user.cliente_id)).first()
        if not quote:
            # Crear cotización temporal si no hay
            print("Creando cotización de prueba...")
            quote = Quote(
                cliente_id=user.cliente_id,
                estado="Enviada",
                total=150.00
            )
            db.add(quote)
            db.commit()
            db.refresh(quote)
        else:
            # Forzar estado a Enviada para poder probar transiciones del cliente
            quote.estado = "Enviada"
            db.add(quote)
            db.commit()
            db.refresh(quote)

        # Simular cambio de estado por el cliente
        quote.estado = "Aprobación Solicitada"
        db.add(quote)
        db.commit()
        db.refresh(quote)
        print(f"OK: Cotización {quote.id} actualizada exitosamente a estado: {quote.estado}")

if __name__ == "__main__":
    test_magic_link_and_status()
