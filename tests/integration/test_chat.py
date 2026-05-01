import uuid


def test_chat_basic(client, base_payload):

    r = client.post("/register", json=base_payload)
    assert r.status_code == 200
    user_id = r.json()["user_id"]

    response = client.post("/chat", json={
        "user_id": user_id,
        "message": "Who am I?"
    })

    assert response.status_code == 200
    assert "answer" in response.json()


def test_chat_context_memory(client, base_payload):

    r = client.post("/register", json=base_payload)
    assert r.status_code == 200
    user_id = r.json()["user_id"]

    client.post("/chat", json={
        "user_id": user_id,
        "message": "My name is John"
    })

    response = client.post("/chat", json={
        "user_id": user_id,
        "message": "What is my name?"
    })

    assert response.status_code == 200
    assert "answer" in response.json()


def test_chat_returns_source(client, base_payload):

    r = client.post("/register", json=base_payload)
    assert r.status_code == 200
    user_id = r.json()["user_id"]

    response = client.post("/chat", json={
        "user_id": user_id,
        "message": "What is my salary?"
    })

    data = response.json()

    assert "source" in data
    assert data["source"] in ["sql", "vector", "unknown"]


def test_audit_log_written(client, base_payload):

    r = client.post("/register", json=base_payload)
    assert r.status_code == 200
    user_id = r.json()["user_id"]

    chat = client.post("/chat", json={
        "user_id": user_id,
        "message": "Check audit"
    })

    assert chat.status_code == 200

    logs = client.get(f"/audit/logs/{user_id}").json()

    assert "logs" in logs
    assert len(logs["logs"]) > 0