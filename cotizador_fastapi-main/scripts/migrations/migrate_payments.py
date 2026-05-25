import sqlite3
import os

db_path = "database.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "ALTER TABLE payment ADD COLUMN cliente_id INTEGER REFERENCES customer(id)"
        )
        print("Columna cliente_id añadida a la tabla payment correctamente.")
    except sqlite3.OperationalError as e:
        print(f"Error o ya existe: {e}")
    conn.commit()
    conn.close()
else:
    print("No se encontró database.db")
