import pytest
import uuid
import tempfile
import os
import sqlite3
from fastapi.testclient import TestClient

import backend.main as main
import backend.app.agent.nodes as nodes
from backend.main import app
from langgraph.checkpoint.sqlite import SqliteSaver


# =================================================
# 1. TEMP DB PER TEST
# =================================================
@pytest.fixture(scope="function")
def temp_db():
    db_fd, db_path = tempfile.mkstemp()

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.executescript("""
    PRAGMA foreign_keys = ON;

    CREATE TABLE users (
        user_id TEXT PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT
    );

    CREATE TABLE employees (
        user_id TEXT PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        phone_number TEXT,
        position TEXT,
        department TEXT,
        location TEXT,
        hire_date TEXT,
        supervisor_id TEXT,
        salary REAL,
        available_pto INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );

    CREATE TABLE employee_skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        skill TEXT,
        FOREIGN KEY(user_id) REFERENCES employees(user_id)
    );

    CREATE TABLE chat_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        question TEXT,
        answer TEXT,
        source_used TEXT,
        node_path TEXT,
        timestamp TEXT
    );
    """)

    import hashlib
    admin_id = "user_9462"
    password_hash = hashlib.sha256("password123".encode()).hexdigest()

    cursor.execute("""
        INSERT INTO users VALUES (?, ?, ?, ?)
    """, (admin_id, "admin_user", password_hash, "admin"))

    # IMPORTANT: also insert into employees (required for supervisor validation)
    cursor.execute("""
    INSERT INTO employees (
        user_id, first_name, last_name, email,
        phone_number, position, department, location,
        hire_date, supervisor_id, salary, available_pto
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
    admin_id,
    "Admin",
    "User",
    "admin@test.com",
    "123456789",
    "Admin",
    "IT",
    "Berlin",
    "2026-01-01",
    None,
    100000,
    30
    ))

    conn.commit()
    conn.close()

    yield db_path

    os.close(db_fd)
    os.unlink(db_path)


# =================================================
# 2. CLIENT FIXTURE
# =================================================
@pytest.fixture(scope="function")
def client(temp_db):

    import backend.main as main
    import backend.app.db.connection as db_connection  # ⭐ IMPORTANT FIX

    def override_get_connection():
        conn = sqlite3.connect(temp_db, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # =================================================
    # FORCE MAIN APP DB
    # =================================================
    main.get_connection = override_get_connection
    main.get_db_connection = override_get_connection

    # =================================================
    # ⭐ CRITICAL FIX: audit logging DB
    # =================================================
    db_connection.get_db_connection = override_get_connection

    # =================================================
    # LangGraph checkpoint isolation (correct)
    # =================================================
    checkpoint_conn = sqlite3.connect(":memory:", check_same_thread=False)
    main.memory = SqliteSaver(checkpoint_conn)

    test_client = TestClient(app)

    yield test_client

    # cleanup
    main.get_connection = None
    main.get_db_connection = None
    db_connection.get_db_connection = None
    main.memory = None


# =================================================
# 3. BASE PAYLOAD
# =================================================
@pytest.fixture
def base_payload():
    return {
        "admin_id": "user_9462",
        "username": f"user_{uuid.uuid4().hex[:8]}",
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "phone_number": "123456789",
        "position": "Engineer",
        "department": "IT",
        "location": "Berlin",
        "hire_date": "2026-04-30",
        "supervisor_id": None,
        "salary": 70000,
        "available_pto": 15,
        "role": "employee",
        "skills": "python, ml"
    }