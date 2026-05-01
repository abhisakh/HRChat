def test_login_success(client, base_payload):

    # Register first
    reg = client.post("/register", json=base_payload)
    assert reg.status_code == 200

    # Login
    r = client.post("/login", json={
        "username": base_payload["username"],
        "password": base_payload["password"]
    })

    assert r.status_code == 200
    assert "user_id" in r.json()


def test_login_fail(client):
    r = client.post("/login", json={
        "username": "invalid_user",
        "password": "wrong"
    })

    assert r.status_code == 401