CREATE TABLE IF NOT EXISTS chat_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    question TEXT,
    answer TEXT,
    source_used TEXT,
    node_path TEXT,  -- <--- NEW ADDITION FOR TIME TRAVEL
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);