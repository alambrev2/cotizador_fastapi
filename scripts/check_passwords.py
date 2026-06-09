"""Test loading user 'cliente' from database."""
import sqlite3

conn = sqlite3.connect("data/database.db")
cursor = conn.execute("SELECT id, username, role, hashed_password FROM user WHERE username = 'cliente'")
row = cursor.fetchone()
print(f"DB row: id={row[0]}, username={row[1]}, role='{row[2]}', hash={row[3][:30]}...")

# Now test with SQLModel
import sys
sys.path.insert(0, ".")
from app.models import RoleEnum

print(f"\nRoleEnum values:")
for r in RoleEnum:
    print(f"  {r.name} = '{r.value}'")

print(f"\nDB role value: '{row[2]}'")
print(f"Expected enum value: '{RoleEnum.CLIENTE.value}'")
print(f"Match: {row[2] == RoleEnum.CLIENTE.value}")

# Try to create enum from DB value
try:
    role = RoleEnum(row[2])
    print(f"Enum created OK: {role}")
except ValueError as e:
    print(f"ENUM ERROR: {e}")
    print("THIS IS THE BUG - the DB has uppercase role names but the enum expects title case!")

conn.close()
