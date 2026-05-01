def test_register_missing_field(client):

    r = client.post("/register", json={})

    assert r.status_code == 422