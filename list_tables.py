import sqlite3

conn = sqlite3.connect('database/brands.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tabelas no banco:")
for t in tables:
    print(f"  - {t}")
conn.close()
