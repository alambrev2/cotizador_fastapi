import sqlite3

db_path = "database.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE accountcharge ADD COLUMN folio_nota VARCHAR")
    print("Columna folio_nota añadida")
except sqlite3.OperationalError as e:
    print(f"Error añadiendo folio_nota: {e}")

try:
    cursor.execute("ALTER TABLE accountcharge ADD COLUMN estatus VARCHAR DEFAULT 'Pendiente'")
    print("Columna estatus añadida")
except sqlite3.OperationalError as e:
    print(f"Error añadiendo estatus: {e}")

# Migrar los existenes que estén documentados
try:
    cursor.execute("UPDATE accountcharge SET estatus = 'Remisión Emitida' WHERE documentado = 1")
    print("Cargos existentes actualizados a 'Remisión Emitida'")
except sqlite3.OperationalError as e:
    print(f"Error actualizando estatus: {e}")

conn.commit()
conn.close()
