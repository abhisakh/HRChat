def test_login_success(client):
    response = client.post("/login", json={
        "username": "colleen",
        "password": "password123"
    })

    assert response.status_code == 200
    assert "user_id" in response.json()


def test_login_fail(client):
    response = client.post("/login", json={
        "username": "wrong_user",
        "password": "wrong_pass"
    })

    assert response.status_code == 401