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

# Migración automática ligera para SQLite
try:
    from sqlalchemy import text
    with engine.begin() as conn:
        res = conn.execute(text("PRAGMA table_info(user)")).fetchall()
        columns = [row[1] for row in res]
        if "magic_token" not in columns:
            conn.execute(text("ALTER TABLE user ADD COLUMN magic_token VARCHAR"))
        if "magic_token_expires" not in columns:
            conn.execute(text("ALTER TABLE user ADD COLUMN magic_token_expires DATETIME"))
except Exception as e:
    print(f"Error checking/altering user table: {e}")


def create_db_and_tables():
    try:
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        print(f"Error creando base de datos: {e}")
        raise


def get_session():
    with Session(engine) as session:
        yield session
