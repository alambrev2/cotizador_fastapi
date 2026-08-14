from sqlmodel import SQLModel, create_engine, Session
import os
from app.core.config import settings
from app.core.paths import DATA_DIR

# Base de datos por defecto: data/database.db
# Se puede apuntar a otra BD con DATABASE_URL en .env (útil para tests y despliegues)
DATA_DIR.mkdir(parents=True, exist_ok=True)
sqlite_url = settings.DATABASE_URL or f"sqlite:///{DATA_DIR / 'database.db'}"

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

        res_sch = conn.execute(text("PRAGMA table_info(scheduledexpense)")).fetchall()
        sch_columns = [row[1] for row in res_sch]
        if "categoria" not in sch_columns:
            conn.execute(text("ALTER TABLE scheduledexpense ADD COLUMN categoria VARCHAR DEFAULT 'General'"))
        if "tipo_gasto" not in sch_columns:
            conn.execute(text("ALTER TABLE scheduledexpense ADD COLUMN tipo_gasto VARCHAR DEFAULT 'Fijo'"))
        if "tipo_dato" not in sch_columns:
            conn.execute(text("ALTER TABLE scheduledexpense ADD COLUMN tipo_dato VARCHAR DEFAULT 'Fijo'"))

        # ── Columnas de trazabilidad de pago en expense ──────────────────────
        res_exp = conn.execute(text("PRAGMA table_info(expense)")).fetchall()
        exp_columns = [row[1] for row in res_exp]
        if "fecha_pago" not in exp_columns:
            conn.execute(text("ALTER TABLE expense ADD COLUMN fecha_pago DATETIME"))
        if "forma_pago" not in exp_columns:
            conn.execute(text("ALTER TABLE expense ADD COLUMN forma_pago VARCHAR DEFAULT 'Efectivo'"))
        if "referencia_pago" not in exp_columns:
            conn.execute(text("ALTER TABLE expense ADD COLUMN referencia_pago VARCHAR"))
        if "responsable" not in exp_columns:
            conn.execute(text("ALTER TABLE expense ADD COLUMN responsable VARCHAR"))

        # ── Columnas de trazabilidad de pago en otherincome ──────────────────
        res_inc = conn.execute(text("PRAGMA table_info(otherincome)")).fetchall()
        inc_columns = [row[1] for row in res_inc]
        if "fecha_pago" not in inc_columns:
            conn.execute(text("ALTER TABLE otherincome ADD COLUMN fecha_pago DATETIME"))
        if "forma_pago" not in inc_columns:
            conn.execute(text("ALTER TABLE otherincome ADD COLUMN forma_pago VARCHAR DEFAULT 'Efectivo'"))
        if "referencia_pago" not in inc_columns:
            conn.execute(text("ALTER TABLE otherincome ADD COLUMN referencia_pago VARCHAR"))
        if "responsable" not in inc_columns:
            conn.execute(text("ALTER TABLE otherincome ADD COLUMN responsable VARCHAR"))

except Exception as e:
    print(f"Error checking/altering tables: {e}")


def create_db_and_tables():
    try:
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        print(f"Error creando base de datos: {e}")
        raise


def get_session():
    with Session(engine) as session:
        yield session
