def test_home_creates_user_and_returns_create_task(client):
    res = client.get("/api/home", headers={"X-Dev-Openid": "user-a"})
    assert res.status_code == 200
    body = res.json()
    assert body["primary_task"]["type"] == "create"
    assert body["quota"]["limit"] == 3
    assert body["quota"]["used"] == 0
    assert body["recent"] == []
    assert body["me"]["streak_days"] == 0
    assert body["me"]["stars"] == 0
    assert body["me"]["completed_count"] == 0


def test_home_prefers_retest_over_continue(client):
    from tests.test_quiz_api import ready_quiz

    quiz = ready_quiz(client)
    for index, question in enumerate(quiz["questions"]):
        chosen = question["answer_index"] if index == 0 else (0 if question["answer_index"] != 0 else 1)
        client.post(
            f"/api/quiz/{quiz['id']}/answer",
            json={"question_id": question["question_id"], "chosen_index": chosen},
        )
    body = client.get("/api/home").json()
    assert body["primary_task"]["type"] == "retest"
    assert body["me"]["completed_count"] == 1
    recent = client.get("/api/quiz/recent").json()
    assert recent["items"]


def test_home_without_header_uses_default_openid(client):
    first = client.get("/api/home")
    second = client.get("/api/home")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["quota"]["used"] == second.json()["quota"]["used"]
