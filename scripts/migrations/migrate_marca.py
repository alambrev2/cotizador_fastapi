import sqlite3


def migrate_product_table():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:
        print("Aplicando migraciones a tabla product...")

        # Agregar columna marca
        try:
            cursor.execute("ALTER TABLE product ADD COLUMN marca VARCHAR")
            print("- Agregado marca")
        except Exception as e:
            print(f"- marca: {e}")

        conn.commit()
        print("\n✅ Migración completada exitosamente.")

    except Exception as e:
        print(f"\n❌ Error crítico en migración: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_product_table()
