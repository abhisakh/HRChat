import uuid


def test_full_flow(client):
    """
    End-to-end:
    register → login → chat → audit log check
    """

    username = f"user_{uuid.uuid4().hex[:8]}"
    password = "password123"

    # =========================================================
    # 1. REGISTER
    # =========================================================
    register_payload = {
        "admin_id": "user_9462",
        "username": username,
        "password": password,
        "first_name": "Flow",
        "last_name": "User",
        "email": "flow@example.com",
        "phone_number": "123456789",
        "position": "Engineer",
        "department": "IT",
        "location": "Berlin",
        "hire_date": "2026-04-30",
        "supervisor_id": None,
        "salary": 60000,
        "available_pto": 15,
        "role": "employee",
        "skills": "python"
    }

    r = client.post("/register", json=register_payload)

    assert r.status_code == 200
    data = r.json()
    assert "user_id" in data

    user_id = data["user_id"]

    # =========================================================
    # 2. LOGIN
    # =========================================================
    login = client.post("/login", json={
        "username": username,
        "password": password
    })

    assert login.status_code == 200
    assert "user_id" in login.json()

    # =========================================================
    # 3. CHAT (this triggers LangGraph + audit log)
    # =========================================================
    chat = client.post("/chat", json={
        "user_id": user_id,
        "message": "Hello, test system"
    })

    assert chat.status_code == 200
    assert "answer" in chat.json()

    # =========================================================
    # 4. AUDIT LOG CHECK
    # =========================================================
    logs = client.get(f"/audit/logs/{user_id}")

    assert logs.status_code == 200

    logs_data = logs.json()

    assert "logs" in logs_data
    assert isinstance(logs_data["logs"], list)

    # IMPORTANT: audit should not be empty after chat
    assert len(logs_data["logs"]) > 0