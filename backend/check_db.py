import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('sendbulletin.db')
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tables in SQLite DB:")
for table in tables:
    print(f"- {table[0]}")

    # Get table schema
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print(f"  Columns: {[col[1] for col in columns]}")

    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cursor.fetchone()[0]
    print(f"  Rows: {count}")

    # Show first few rows if any
    if count > 0:
        cursor.execute(f"SELECT * FROM {table[0]} LIMIT 5")
        rows = cursor.fetchall()
        print(f"  Sample data: {rows[:2]}")
    print()

conn.close()
