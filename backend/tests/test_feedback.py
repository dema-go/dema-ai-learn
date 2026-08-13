from tests.test_quiz_api import ready_quiz


def test_submit_question_feedback(client):
    quiz = ready_quiz(client)
    question_id = quiz["questions"][0]["question_id"]
    res = client.post(
        f"/api/question/{question_id}/feedback",
        json={"error_type": "no_evidence"},
    )
    assert res.status_code == 200
    assert res.json()["ok"] is True
    again = client.post(
        f"/api/question/{question_id}/feedback",
        json={"error_type": "no_evidence"},
    )
    assert again.status_code == 200
