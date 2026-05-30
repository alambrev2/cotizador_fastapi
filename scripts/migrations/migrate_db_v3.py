import sqlite3
import os

# Obtener el directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
db_path = os.path.join(BASE_DIR, "data", "database.db")


def migrate_v2():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Aplicando migraciones V2...")

        # 1. Agregar costo a product
        try:
            cursor.execute(
                "ALTER TABLE product ADD COLUMN costo NUMERIC(10, 2) DEFAULT 0"
            )
            print("- Agregado costo a product")
        except Exception as e:
            print(f"- costo: {e}")

        # 2. Crear tabla expense
        try:
            cursor.execute("""
                CREATE TABLE expense (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    descripcion VARCHAR NOT NULL,
                    monto NUMERIC(10, 2) DEFAULT 0,
                    fecha DATETIME,
                    categoria VARCHAR DEFAULT 'Gasto General'
                )
            """)
            print("- Creada tabla expense (MySQL style)")
        except Exception as e:
            # SQLite uses AUTOINCREMENT and slightly different syntax
            try:
                cursor.execute("""
                    CREATE TABLE expense (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        descripcion VARCHAR NOT NULL,
                        monto NUMERIC(10, 2) DEFAULT 0,
                        fecha DATETIME,
                        categoria VARCHAR DEFAULT 'Gasto General'
                    )
                """)
                print("- Creada tabla expense (SQLite style)")
            except Exception as e2:
                print(f"- expense table: {e2}")

        conn.commit()
        print("\n✅ Migraciones V2 completadas exitosamente.")

    except Exception as e:
        print(f"\n❌ Error crítico en migración: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_v2()
