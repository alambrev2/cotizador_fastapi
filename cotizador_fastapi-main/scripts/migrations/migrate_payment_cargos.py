import sqlite3

def migrate():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        print("Agregando columna cargo_id a la tabla payment...")
        cursor.execute("ALTER TABLE payment ADD COLUMN cargo_id INTEGER REFERENCES accountcharge(id);")
        conn.commit()
        print("Migración completada exitosamente.")
    except sqlite3.OperationalError as e:
        print(f"Error o la columna ya existe: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    migrate()
