SAMPLE = "人们常常通过拖延来暂时逃避任务引发的焦虑、无聊或自我怀疑。" * 20


def test_generate_returns_task_immediately(client):
    res = client.post(
        "/api/quiz/generate",
        json={"source_type": "text", "text": SAMPLE},
    )
    assert res.status_code == 200
    task_id = res.json()["task_id"]
    polled = client.get(f"/api/quiz/task/{task_id}")
    assert polled.status_code == 200
    body = polled.json()
    assert body["status"] in {
        "pending",
        "extracting",
        "planning",
        "generating",
        "validating",
        "succeeded",
        "degraded",
        "failed",
    }
    assert body["progress"]
    assert body["task_id"] == task_id


def test_task_not_visible_to_other_user(client):
    res = client.post(
        "/api/quiz/generate",
        json={"source_type": "text", "text": SAMPLE},
        headers={"X-Dev-Openid": "owner"},
    )
    task_id = res.json()["task_id"]
    other = client.get(
        f"/api/quiz/task/{task_id}",
        headers={"X-Dev-Openid": "intruder"},
    )
    assert other.status_code == 404
