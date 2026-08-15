import time

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.tables import Answer, Attempt, User

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


def test_duplicate_answer_returns_stored_result_without_scoring_twice(client, db_session):
    quiz = ready_quiz(client)
    first = quiz["questions"][0]
    payload = {
        "question_id": first["question_id"],
        "chosen_index": first["answer_index"],
    }

    first_res = client.post(f"/api/quiz/{quiz['id']}/answer", json=payload)
    assert first_res.status_code == 200
    first_body = first_res.json()

    replay = client.post(
        f"/api/quiz/{quiz['id']}/answer",
        json={
            **payload,
            "chosen_index": (first["answer_index"] + 1) % len(first["options"]),
        },
    )
    assert replay.status_code == 200
    replay_body = replay.json()
    assert replay_body["attempt_id"] == first_body["attempt_id"]
    assert replay_body["is_correct"] is True
    assert replay_body["correct_index"] == first["answer_index"]
    attempt = db_session.query(Attempt).filter(Attempt.id == first_body["attempt_id"]).one()
    user = db_session.query(User).filter(User.id == attempt.user_id).one()
    assert db_session.query(Answer).filter(Answer.attempt_id == attempt.id).count() == 1
    assert attempt.score == 1
    assert user.stars == 1

    last = None
    for question in quiz["questions"][1:]:
        last = client.post(
            f"/api/quiz/{quiz['id']}/answer",
            json={
                "attempt_id": first_body["attempt_id"],
                "question_id": question["question_id"],
                "chosen_index": question["answer_index"],
            },
        )
    assert last is not None
    assert last.json()["result"]["correct"] == len(quiz["questions"])

    last_question = quiz["questions"][-1]
    completed_replay = client.post(
        f"/api/quiz/{quiz['id']}/answer",
        json={
            "question_id": last_question["question_id"],
            "chosen_index": last_question["answer_index"],
        },
    )
    assert completed_replay.status_code == 200
    assert completed_replay.json()["result"]["correct"] == len(quiz["questions"])
    db_session.refresh(attempt)
    db_session.refresh(user)
    assert (
        db_session.query(Answer).filter(Answer.attempt_id == attempt.id).count()
        == len(quiz["questions"])
    )
    assert attempt.score == len(quiz["questions"])
    assert user.stars == len(quiz["questions"])


def test_attempt_question_rejects_duplicate_answer_rows(client, db_session):
    quiz = ready_quiz(client)
    first = quiz["questions"][0]
    response = client.post(
        f"/api/quiz/{quiz['id']}/answer",
        json={"question_id": first["question_id"], "chosen_index": first["answer_index"]},
    )
    assert response.status_code == 200

    db_session.add(
        Answer(
            attempt_id=response.json()["attempt_id"],
            question_id=first["question_id"],
            chosen_index=(first["answer_index"] + 1) % len(first["options"]),
            is_correct=False,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


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
