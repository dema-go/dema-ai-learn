import time

SOURCE = (
    "研究者认为，人们常常通过拖延来暂时逃避任务引发的焦虑、无聊或自我怀疑。"
    "这种短期情绪修复，会带来更大的长期压力。"
    "拖延并不总是时间管理问题，它也可能是一种回避策略。"
    "短期轻松之后，任务压力往往会变得更大。"
    "理解诱因，有助于把注意力从自责转向调节情绪。"
    "因此读完材料后，用几道题检查自己是否抓住了核心观点。"
)


def wait_task(client, task_id: str, timeout: float = 2.0) -> dict:
    deadline = time.time() + timeout
    body = {}
    while time.time() < deadline:
        body = client.get(f"/api/quiz/task/{task_id}").json()
        if body.get("status") in {"succeeded", "degraded", "failed"}:
            return body
        time.sleep(0.05)
    return body


def ready_quiz(client) -> dict:
    res = client.post("/api/quiz/generate", json={"source_type": "text", "text": SOURCE})
    body = wait_task(client, res.json()["task_id"])
    assert body["status"] in {"succeeded", "degraded"}, body
    return client.get(f"/api/quiz/{body['quiz_id']}").json()


def test_generate_completes_and_quiz_readable(client):
    quiz = ready_quiz(client)
    assert 5 <= len(quiz["questions"]) <= 7
    assert all(item["source_span"] for item in quiz["questions"])
    assert quiz["ai_notice"]
    assert "掌握" not in quiz["ai_notice"]


def test_answer_correct_and_wrong(client):
    quiz = ready_quiz(client)
    first = quiz["questions"][0]
    res = client.post(
        f"/api/quiz/{quiz['id']}/answer",
        json={"question_id": first["question_id"], "chosen_index": first["answer_index"]},
    )
    assert res.status_code == 200
    assert res.json()["is_correct"] is True
    assert res.json()["explanation"]
    assert res.json()["source_span"]
    second = quiz["questions"][1]
    wrong_index = 0 if second["answer_index"] != 0 else 1
    res = client.post(
        f"/api/quiz/{quiz['id']}/answer",
        json={"question_id": second["question_id"], "chosen_index": wrong_index},
    )
    assert res.status_code == 200
    assert res.json()["is_correct"] is False
    assert res.json()["correct_index"] == second["answer_index"]


def test_duplicate_answer_rejected(client):
    quiz = ready_quiz(client)
    first = quiz["questions"][0]
    payload = {"question_id": first["question_id"], "chosen_index": 0}
    first_res = client.post(f"/api/quiz/{quiz['id']}/answer", json=payload)
    assert first_res.status_code == 200
    second_res = client.post(f"/api/quiz/{quiz['id']}/answer", json=payload)
    assert second_res.status_code == 409
    assert second_res.json()["error"]["code"] == "ALREADY_ANSWERED"


def test_finish_quiz_returns_result(client):
    quiz = ready_quiz(client)
    last = None
    for question in quiz["questions"]:
        last = client.post(
            f"/api/quiz/{quiz['id']}/answer",
            json={
                "question_id": question["question_id"],
                "chosen_index": question["answer_index"],
            },
        )
    assert last is not None
    body = last.json()
    assert body["finished"] is True
    assert body["result"]["correct"] == len(quiz["questions"])
    assert body["result"]["total"] == len(quiz["questions"])
    assert body["result"]["wrong_question_ids"] == []

