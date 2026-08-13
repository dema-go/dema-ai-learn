from tests.test_quiz_api import ready_quiz


def test_delete_material_hides_quiz(client):
    quiz = ready_quiz(client)
    res = client.delete(f"/api/material/{quiz['material_id']}")
    assert res.status_code == 200
    missing = client.get(f"/api/quiz/{quiz['id']}")
    assert missing.status_code == 404
