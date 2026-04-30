def test_chat_basic(client):
    response = client.post("/chat", json={
        "user_id": "user_9462",
        "message": "Who am I?"
    })

    assert response.status_code == 200
    assert "answer" in response.json()