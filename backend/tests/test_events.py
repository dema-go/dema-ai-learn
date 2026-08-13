def test_track_event(client):
    res = client.post("/api/events", json={"name": "quiz_started", "payload": {"quiz_id": "x"}})
    assert res.status_code == 200
    assert res.json()["ok"] is True
