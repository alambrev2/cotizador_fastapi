import sqlite3


def check_quote_schema():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    print("Columnas en tabla quote:")
    try:
        cursor.execute("PRAGMA table_info(quote)")
        columns = cursor.fetchall()
        col_names = [col[1] for col in columns]
        for col in columns:
            print(f"- {col[1]} ({col[2]})")

        required = [
            "tipo_pago",
            "fecha_inicio_pago",
            "fecha_fin_pago",
            "plazo_semanas",
            "monto_semanal",
        ]
        missing = [req for req in required if req not in col_names]

        if missing:
            print(f"\n❌ FALTAN COLUMNAS: {missing}")
        else:
            print("\n✅ Esquema correcto.")

    except Exception as e:
        print(e)
    finally:
        conn.close()


if __name__ == "__main__":
    check_quote_schema()
