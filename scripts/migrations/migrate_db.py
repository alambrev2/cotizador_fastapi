import sqlite3


def migrate_quote_table():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:
        print("Aplicando migraciones a tabla quote...")

        # Agregar columnas una por una
        try:
            cursor.execute(
                "ALTER TABLE quote ADD COLUMN tipo_pago VARCHAR DEFAULT 'Contado'"
            )
            print("- Agregado tipo_pago")
        except Exception as e:
            print(f"- tipo_pago: {e}")

        try:
            cursor.execute("ALTER TABLE quote ADD COLUMN fecha_inicio_pago DATE")
            print("- Agregado fecha_inicio_pago")
        except Exception as e:
            print(f"- fecha_inicio_pago: {e}")

        try:
            cursor.execute("ALTER TABLE quote ADD COLUMN fecha_fin_pago DATE")
            print("- Agregado fecha_fin_pago")
        except Exception as e:
            print(f"- fecha_fin_pago: {e}")

        try:
            cursor.execute(
                "ALTER TABLE quote ADD COLUMN plazo_semanas INTEGER DEFAULT 0"
            )
            print("- Agregado plazo_semanas")
        except Exception as e:
            print(f"- plazo_semanas: {e}")

        try:
            cursor.execute(
                "ALTER TABLE quote ADD COLUMN monto_semanal NUMERIC(10, 2) DEFAULT 0"
            )
            print("- Agregado monto_semanal")
        except Exception as e:
            print(f"- monto_semanal: {e}")

        conn.commit()
        print("\n✅ Migración completada exitosamente.")

    except Exception as e:
        print(f"\n❌ Error crítico en migración: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_quote_table()
