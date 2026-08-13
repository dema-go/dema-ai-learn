SAMPLE = "人们常常通过拖延来暂时逃避任务引发的焦虑、无聊或自我怀疑。" * 20


def test_reject_text_over_8000(client):
    res = client.post(
        "/api/quiz/generate",
        json={"source_type": "text", "text": "测" * 8001},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "TEXT_TOO_LONG"
    assert "截取" in res.json()["error"]["message"]


def test_reject_empty_text(client):
    res = client.post("/api/quiz/generate", json={"source_type": "text", "text": "   "})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "TEXT_EMPTY"


def test_accept_text_8000(client):
    res = client.post(
        "/api/quiz/generate",
        json={"source_type": "text", "text": "测" * 8000},
    )
    assert res.status_code == 200
    assert "task_id" in res.json()


def test_reject_invalid_url(client):
    res = client.post(
        "/api/quiz/generate",
        json={"source_type": "url", "url": "not-a-url"},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "URL_INVALID"


def test_reject_url_without_value(client):
    res = client.post("/api/quiz/generate", json={"source_type": "url"})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "URL_REQUIRED"
