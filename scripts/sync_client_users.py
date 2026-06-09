import sys
import os

# Add app to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.database import engine
from app.models import User, Customer, RoleEnum
from app.core.security import get_password_hash

def sync_users():
    with Session(engine) as session:
        customers = session.exec(select(Customer)).all()
        created = 0
        
        for customer in customers:
            # Check if user already exists for this email
            existing_user = session.exec(select(User).where(User.email == customer.email)).first()
            if not existing_user:
                # generate unique username
                base_username = customer.email.split('@')[0] if customer.email else customer.nombre.lower().replace(" ", "")
                username = base_username
                counter = 1
                while session.exec(select(User).where(User.username == username)).first():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                new_user = User(
                    username=username,
                    email=customer.email,
                    role=RoleEnum.CLIENTE,
                    hashed_password=get_password_hash("cliente123"),
                    cliente_id=customer.id
                )
                session.add(new_user)
                created += 1
                print(f"Creado usuario para {customer.nombre}: Usuario={username}, Contraseña=cliente123")
            else:
                # If user exists but is not linked, link it
                if not existing_user.cliente_id:
                    existing_user.cliente_id = customer.id
                    session.add(existing_user)
                    print(f"Vinculado usuario existente {existing_user.username} con cliente {customer.nombre}")
        
        session.commit()
        print(f"Sincronización terminada. {created} nuevos usuarios creados.")

if __name__ == "__main__":
    sync_users()
