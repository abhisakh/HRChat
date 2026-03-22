-- Schema for User Authentication
-- CREATE TABLE IF NOT EXISTS users (
--     user_id TEXT PRIMARY KEY,
--     username TEXT UNIQUE NOT NULL,
--     password_hash TEXT NOT NULL,
--     role TEXT DEFAULT 'employee',
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (user_id) REFERENCES employees(user_id)
-- );


CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'employee' CHECK(role IN ('employee', 'hr', 'admin')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES employees(user_id)
);