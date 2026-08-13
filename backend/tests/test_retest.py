from tests.test_quiz_api import SOURCE, ready_quiz


def test_retest_contains_only_wrong_questions(client):
    quiz = ready_quiz(client)
    wrong_ids = []
    for index, question in enumerate(quiz["questions"]):
        chosen = question["answer_index"] if index == 0 else (0 if question["answer_index"] != 0 else 1)
        client.post(
            f"/api/quiz/{quiz['id']}/answer",
            json={"question_id": question["question_id"], "chosen_index": chosen},
        )
        if chosen != question["answer_index"]:
            wrong_ids.append(question["question_id"])
    res = client.post(f"/api/quiz/{quiz['id']}/retest")
    assert res.status_code == 200
    retest = client.get(f"/api/quiz/{res.json()['quiz_id']}").json()
    assert retest["is_retest"] is True
    assert len(retest["questions"]) == len(wrong_ids)
    assert {item["stem"] for item in retest["questions"]}


def test_retest_without_wrong_answers(client):
    quiz = ready_quiz(client)
    for question in quiz["questions"]:
        client.post(
            f"/api/quiz/{quiz['id']}/answer",
            json={
                "question_id": question["question_id"],
                "chosen_index": question["answer_index"],
            },
        )
    res = client.post(f"/api/quiz/{quiz['id']}/retest")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "NO_WRONG_ANSWERS"
