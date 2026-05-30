import sqlite3


def check_schema():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    print("Columnas en tabla product:")
    try:
        cursor.execute("PRAGMA table_info(product)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
    except Exception as e:
        print(e)
    finally:
        conn.close()


if __name__ == "__main__":
    check_schema()
