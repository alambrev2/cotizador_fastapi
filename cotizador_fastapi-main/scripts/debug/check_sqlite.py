import sqlite3
c = sqlite3.connect('data/database.db')
r = c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='scheduledexpense'").fetchone()
if r:
    print(r[0])
else:
    print('No table found')
