def test_register_missing_field(client):
    response = client.post("/register", json={
        "username": "broken_user",
        "password": "password123"
    })

    assert response.status_code == 422