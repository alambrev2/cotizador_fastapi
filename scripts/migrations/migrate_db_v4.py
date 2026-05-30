import sqlite3
import os

# Obtener el directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
db_path = os.path.join(BASE_DIR, "data", "database.db")


def migrate_v4():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Aplicando migraciones V4 (Other Income)...")

        # Crear tabla other_income
        try:
            cursor.execute("""
                CREATE TABLE otherincome (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descripcion VARCHAR NOT NULL,
                    monto NUMERIC(10, 2) DEFAULT 0,
                    fecha DATETIME,
                    categoria VARCHAR DEFAULT 'Ingreso General'
                )
            """)
            print("- Creada tabla otherincome")
        except Exception as e:
            print(f"- otherincome table: {e}")

        conn.commit()
        print("\n✅ Migraciones V4 completadas exitosamente.")

    except Exception as e:
        print(f"\n❌ Error crítico en migración: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_v4()
