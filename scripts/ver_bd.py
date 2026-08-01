"""Ver las tablas y consultar la BD SQLite del proyecto desde la terminal."""
import sqlite3
import sys

DB = r"C:\Users\Alan Alcantara\OneDrive\Escritorio\cotizador_fastapi\data\database.db"

conn = sqlite3.connect(DB)
cursor = conn.cursor()

def listar_tablas():
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [r[0] for r in cursor.fetchall()]

def ver_tabla(tabla):
    cursor.execute(f'SELECT * FROM "{tabla}" LIMIT 50')
    rows = cursor.fetchall()
    colnames = [d[0] for d in cursor.description]
    print(f"\n=== {tabla} ({len(rows)} filas mostradas) ===")
    print(" | ".join(colnames))
    for r in rows:
        print(" | ".join(str(v)[:40] for v in r))

if len(sys.argv) > 1:
    ver_tabla(sys.argv[1])
else:
    print("Tablas disponibles:")
    for t in listar_tablas():
        cursor.execute(f'SELECT COUNT(*) FROM "{t}"')
        print(f"  - {t}  ({cursor.fetchone()[0]} filas)")

conn.close()
