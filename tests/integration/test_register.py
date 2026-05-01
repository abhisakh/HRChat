import uuid


def test_register_success(client, base_payload):

    payload = base_payload.copy()

    r = client.post("/register", json=payload)

    assert r.status_code == 200
    assert "user_id" in r.json()


def test_register_duplicate_username(client, base_payload):

    payload = base_payload.copy()

    r1 = client.post("/register", json=payload)
    r2 = client.post("/register", json=payload)

    assert r1.status_code == 200
    assert r2.status_code == 400


def test_register_with_supervisor(client, base_payload):

    payload = base_payload.copy()
    payload["supervisor_id"] = "user_9462"

    r = client.post("/register", json=payload)

    assert r.status_code == 200
    assert "user_id" in r.json()


def test_register_without_skills(client, base_payload):

    payload = base_payload.copy()
    payload["skills"] = ""

    r = client.post("/register", json=payload)

    assert r.status_code == 200
    assert "user_id" in r.json()


def test_register_invalid_admin(client):

    response = client.post("/register", json={
        "admin_id": "invalid_user",
        "username": "bad_user",
        "password": "password123",
        "first_name": "Bad",
        "last_name": "User",
        "email": "bad@example.com",
        "phone_number": "123",
        "position": "Engineer",
        "department": "IT",
        "location": "Berlin",
        "hire_date": "2026-04-30",
        "supervisor_id": None,
        "salary": 50000,
        "available_pto": 10,
        "role": "employee",
        "skills": "python"
    })

    assert response.status_code == 403


def test_register_with_invalid_supervisor(client, base_payload):

    payload = base_payload.copy()
    payload["username"] = f"user_{uuid.uuid4().hex[:6]}"
    payload["supervisor_id"] = "non_existing"

    response = client.post("/register", json=payload)

    assert response.status_code in [200, 400]