import sys
import os

# Add app to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, SQLModel
from app.database import engine
from app.models import User, RoleEnum
from app.core.security import get_password_hash

def create_users():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Check if users already exist
        if session.query(User).first():
            print("Users already exist. Skipping creation.")
            return

        admin = User(
            username="admin",
            email="admin@example.com",
            role=RoleEnum.Administrador,
            hashed_password=get_password_hash("admin123")
        )
        
        operativo = User(
            username="operativo",
            email="operativo@example.com",
            role=RoleEnum.Operativo,
            hashed_password=get_password_hash("operativo123")
        )
        
        cliente = User(
            username="cliente",
            email="cliente@example.com",
            role=RoleEnum.Cliente,
            hashed_password=get_password_hash("cliente123")
        )
        
        session.add(admin)
        session.add(operativo)
        session.add(cliente)
        session.commit()
        print("Initial users created successfully:")
        print("- admin / admin123")
        print("- operativo / operativo123")
        print("- cliente / cliente123")

if __name__ == "__main__":
    create_users()
