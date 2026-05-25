from sqlmodel import SQLModel, create_engine, Session
import os

# Obtener el directorio base del proyecto (directorio padre de app)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sqlite_file_name = os.path.join(BASE_DIR, "data", "database.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"

# Asegurar que el directorio data exista
os.makedirs(os.path.dirname(sqlite_file_name), exist_ok=True)

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    try:
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        print(f"Error creando base de datos: {e}")
        raise


def get_session():
    with Session(engine) as session:
        yield session
