import sqlite3
from pathlib import Path

# Update this path to your actual hr_database.db
db_path = Path("backend/app/db/hr_database.db")

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA journal_mode=WAL;") # Permanent fix for "locked" errors
conn.close()
print("Database is now in WAL mode. Concurrency enabled.")