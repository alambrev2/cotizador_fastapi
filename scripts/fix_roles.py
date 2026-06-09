"""Fix role values in database to match RoleEnum."""
import sqlite3

conn = sqlite3.connect("data/database.db")

# Show current state
print("Before fix:")
cursor = conn.execute("SELECT id, username, role FROM user")
for row in cursor.fetchall():
    print(f"  {row}")

# Fix roles
conn.execute("UPDATE user SET role = 'Administrador' WHERE role = 'ADMINISTRADOR'")
conn.execute("UPDATE user SET role = 'Operativo' WHERE role = 'OPERATIVO'")
conn.execute("UPDATE user SET role = 'Cliente' WHERE role = 'CLIENTE'")
conn.commit()

# Show fixed state
print("\nAfter fix:")
cursor = conn.execute("SELECT id, username, role FROM user")
for row in cursor.fetchall():
    print(f"  {row}")

conn.close()
print("\nDone! Roles fixed successfully.")
