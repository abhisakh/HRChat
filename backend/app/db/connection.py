# backend/app/db/connection.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "hr_database.db"
SCHEMA_DIR = Path(__file__).parent / "schemas"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    # Execute all schemas found in the schemas folder
    for schema_file in SCHEMA_DIR.glob("*.sql"):
        with open(schema_file, "r") as f:
            conn.executescript(f.read())
    conn.commit()
    conn.close()

def save_to_audit_log(user_id, question, answer, source, node_path):
    """Saves the interaction details with the AI decision path."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_audit_logs (user_id, question, answer, source_used, node_path)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, question, answer, source, node_path))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Logging Error: {e}")