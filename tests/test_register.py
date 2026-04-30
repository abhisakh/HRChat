import uuid

def test_register_duplicate_username(client):
    username = f"dup_user_{uuid.uuid4().hex[:6]}"

    payload = {
        "admin_id": "user_9462",
        "username": username,
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
        "email": "test2@example.com",
        "phone_number": "123456789",
        "position": "Engineer",
        "department": "IT",
        "location": "Berlin",
        "hire_date": "2026-04-30",
        "supervisor_id": None,
        "salary": 70000,
        "available_pto": 15,
        "role": "employee",
        "skills": "python"
    }

    # first insert → must succeed
    r1 = client.post("/register", json=payload)
    assert r1.status_code == 200

    # second insert → must fail
    r2 = client.post("/register", json=payload)
    assert r2.status_code == 400