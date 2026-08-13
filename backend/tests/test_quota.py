def _payload(seed: str) -> dict:
    return {
        "source_type": "text",
        "text": f"{seed}：" + "内容足够长的一段话，用来生成闯关题目。" * 20,
    }


def test_fourth_generate_is_rejected(client):
    for i in range(3):
        res = client.post("/api/quiz/generate", json=_payload(f"材料{i}"))
        assert res.status_code == 200, res.text
    res = client.post("/api/quiz/generate", json=_payload("第四篇"))
    assert res.status_code == 429
    assert res.json()["error"]["code"] == "QUOTA_EXCEEDED"
    assert res.json()["error"]["message"]


def test_same_hash_does_not_consume_quota(client):
    payload = {
        "source_type": "text",
        "text": "拖延是一种短期情绪调节策略。" * 30,
    }
    first = client.post("/api/quiz/generate", json=payload)
    second = client.post("/api/quiz/generate", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    home = client.get("/api/home").json()
    assert home["quota"]["used"] == 1
    assert first.json()["task_id"] == second.json()["task_id"]


def test_cache_not_shared_across_users(client):
    payload = {
        "source_type": "text",
        "text": "同一段公开资料内容。" * 40,
    }
    a = client.post(
        "/api/quiz/generate",
        json=payload,
        headers={"X-Dev-Openid": "u1"},
    )
    b = client.post(
        "/api/quiz/generate",
        json=payload,
        headers={"X-Dev-Openid": "u2"},
    )
    assert a.status_code == 200
    assert b.status_code == 200
    assert a.json()["task_id"] != b.json()["task_id"]
