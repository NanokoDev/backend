import pytest

from .resources import llm_api_callback


question_id_cache = None
sub_question_id_cache = None


@pytest.fixture(scope="module")
def question_id(client, admin_token):
    """Get a sub question id, if not exist, create one

    Args:
        client (TestClient): The test client
        admin_token (str): The admin token
    """
    global question_id_cache
    if question_id_cache is not None:
        return question_id_cache
    question = {
        "source": "testing",
        "sub_questions": [
            {
                "description": "This is a test subquestion without image",
                "answer": "This is a standard answer to the subquestion",
                "concept": 0,
                "process": 0,
            },
        ],
    }
    response = client.post(
        "/api/v1/bank/question/add",
        json=question,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, f"Failed to create question: {response.content}"
    question_id = response.json()["question_id"]
    question_id_cache = question_id

    # approve the question
    response = client.post(
        "/api/v1/bank/question/approve",
        json={"question_id": question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to approve question: {response.content}"
    )

    return question_id_cache


@pytest.fixture(scope="module")
def sub_question_id(client, admin_token, question_id):
    """Get a sub question id, if not exist, create one

    Args:
        client (TestClient): The test client
        admin_token (str): The admin token
        question_id (int): The question id

    Returns:
        int: The sub question id
    """
    global sub_question_id_cache
    if sub_question_id_cache is not None:
        return sub_question_id_cache
    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_id": question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, f"Failed to get question: {response.content}"
    sub_question_id = response.json()[0]["sub_questions"][0]["id"]
    sub_question_id_cache = sub_question_id
    return sub_question_id_cache


def test_get_hint(client, student_token, httpx_mock):
    """Test api/v1/llm/hint endpoint

    Args:
        client (TestClient): The test client
        student_token (str): The student token
        httpx_mock (HTTPXMock): The HTTPX mocker
    """
    httpx_mock.add_callback(llm_api_callback, method="POST", is_reusable=True)

    # Expected cases
    response = client.get(
        "/api/v1/llm/hint",
        headers={"Authorization": f"Bearer {student_token}"},
        params={
            "sub_question_id": 1,
            "question": "I dont have any idea about this question",
        },
    )
    assert response.status_code == 200, f"Failed to get hint: {response.content}"
    assert response.json().get("hint"), f"Hint is empty: {response.content}"

    # Boundary cases
    response = client.get(
        "/api/v1/llm/hint",
        headers={"Authorization": f"Bearer {student_token}"},
        params={
            "sub_question_id": 112012,
            "question": "I dont have any idea about this question",
        },
    )
    assert response.status_code == 404, f"Failed to get 404: {response.content}"

    response = client.get(
        "/api/v1/llm/hint",
        params={
            "sub_question_id": 1,
            "question": "I dont have any idea about this question",
        },
    )
    assert response.status_code == 401, f"Failed to get 401: {response.content}"

    # Unexpected cases
    response = client.post(
        "/api/v1/llm/hint",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "sub_question_id": 1,
            "question": "I dont have any idea about this question",
        },
    )
    assert response.status_code == 405, f"Failed to get 405: {response.content}"
