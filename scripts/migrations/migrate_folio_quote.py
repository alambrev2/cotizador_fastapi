import sqlite3

db_path = "database.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE quote RENAME COLUMN folio TO folio_cotizacion")
    print("Columna renombrada exitosamente")
except sqlite3.OperationalError as e:
    print(f"Error renombrando folio_cotizacion: {e}")

conn.commit()
conn.close()
