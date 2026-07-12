async def test_ask_transitops(client, seed_vehicle, seed_driver):
    resp = await client.post(
        "/api/v1/chat/ask",
        json={"question": "How many vehicles do we have?"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert isinstance(data["answer"], str)


async def test_ask_empty_fleet(client):
    resp = await client.post(
        "/api/v1/chat/ask",
        json={"question": "List all drivers"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data


async def test_ask_validation_error(client):
    resp = await client.post(
        "/api/v1/chat/ask",
        json={"question": ""},
    )
    assert resp.status_code == 422
