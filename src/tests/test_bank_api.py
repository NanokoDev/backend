import pytest
from pathlib import Path

import backend.config as cfg
from backend.types.question import ConceptType, ProcessType


@pytest.fixture(scope="module")
def test_image_path():
    """Get the test image path

    Returns:
        Path: the path to the test image
    """
    return Path("src/tests/test_image.png")


@pytest.fixture(scope="module")
def uploaded_image_hash(client, test_image_path, admin_token):
    """Upload a test image and return its hash

    Args:
        client (TestClient): the test client
        test_image_path (Path): the path to the test image
        admin_token (str): the admin token

    Returns:
        str: the hash of the uploaded image
    """
    with open(test_image_path, "rb") as f:
        files = {"file": (test_image_path.name, f, "image/png")}
        response = client.post(
            "/api/v1/bank/image/upload",
            files=files,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    assert response.status_code == 200, response.content
    return response.json()["hash"]


@pytest.fixture(scope="module")
def image_id(client, uploaded_image_hash, admin_token):
    """Upload an image and return its ID

    Args:
        client (TestClient): the test client
        uploaded_image_hash (_type_): the hash of the uploaded image
        admin_token (str): the admin token

    Returns:
        int: the ID of the uploaded image
    """
    response = client.post(
        "/api/v1/bank/image/add",
        json={"description": "A Test Image", "hash": uploaded_image_hash},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    return response.json()["image_id"]


@pytest.fixture(scope="module")
def question_id(client, image_id, admin_token):
    """Add a question and return its ID

    Args:
        client (TestClient): the test client
        image_id (int): the ID of the uploaded image
        admin_token (str): the admin token

    Returns:
        int: the ID of the added question
    """
    question = {
        "source": "testing",
        "sub_questions": [
            {
                "description": "This is a test subquestion without image",
                "answer": "This is a standard answer to the subquestion",
                "concept": ConceptType.ELEMENTS_OF_CHANCE.value,
                "process": ProcessType.APPLY.value,
            },
            {
                "description": "This is test subquestion with image",
                "answer": "This is a standard answer to the subquestion",
                "concept": ConceptType.ELEMENTS_OF_CHANCE.value,
                "process": ProcessType.EXPLAIN.value,
                "image_id": image_id,
            },
        ],
    }
    response = client.post(
        "/api/v1/bank/question/add",
        json=question,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    return response.json()["question_id"]


def test_image_upload(client, test_image_path, student_token, admin_token):
    """Test the image upload endpoint

    Args:
        client (TestClient): the test client
        test_image_path (Path): the path to the test image
        student_token (str): the student token
        admin_token (str): the admin token
    """
    with open(test_image_path, "rb") as f:
        # Expected cases
        files = {"file": (test_image_path.name, f, "image/png")}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            "/api/v1/bank/image/upload", files=files, headers=headers
        )
        assert response.status_code == 200, response.content
        assert response.json()["hash"]
        assert (
            cfg.config.image_store_path / "95d17bdeaca5d43432576b71043ef9f8.png"
        ).exists()

        # Boundary cases
        files = {"file": (test_image_path.name, f, "image/gif")}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            "/api/v1/bank/image/upload", files=files, headers=headers
        )
        assert response.status_code == 415, response.content
        assert "unsupported content_type" in response.json()["detail"].lower()

        files = {"file": (test_image_path.name, f, "image/png")}
        headers = {"Authorization": f"Bearer {student_token}"}
        response = client.post(
            "/api/v1/bank/image/upload", files=files, headers=headers
        )
        assert response.status_code == 403, response.content

        files = {"file": (test_image_path.name, f, "image/png")}
        response = client.post("/api/v1/bank/image/upload", files=files)
        assert response.status_code == 401, response.content

        # Unexpected cases
        response = client.post(
            "/api/v1/bank/image/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422, response.content


def test_image_add(client, uploaded_image_hash, student_token, admin_token):
    """Test the image add endpoint

    Args:
        client (TestClient): the test client
        uploaded_image_hash (str): the hash of the uploaded image
        student_token (str): the student token
        admin_token (str): the admin token
    """
    # Expected cases
    response = client.post(
        "/api/v1/bank/image/add",
        json={"description": "A Test Image", "hash": uploaded_image_hash},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json()["image_id"]

    # Boundary cases
    response = client.post(
        "/api/v1/bank/image/add",
        json={"description": "Unexist image", "hash": "1" * 32},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content
    assert response.json()["detail"]

    response = client.post(
        "/api/v1/bank/image/add",
        json={"description": "A Test Image", "hash": uploaded_image_hash},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, response.content

    response = client.post(
        "/api/v1/bank/image/add",
        json={"description": "A Test Image", "hash": uploaded_image_hash},
    )
    assert response.status_code == 401, response.content

    # Unexpected cases
    response = client.post(
        "/api/v1/bank/image/add", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422, response.content

    response = client.get(
        "/api/v1/bank/image/add",
        params={"description": "A Test Image", "hash": uploaded_image_hash},
    )
    assert response.status_code == 405, response.content


def test_image_get(client, image_id, student_token):
    """Test the image get endpoint

    Args:
        client (TestClient): the test client
        image_id (int): the ID of the uploaded image
        student_token (str): the student token
    """
    # Expected cases
    response = client.get(
        "/api/v1/bank/image/get",
        params={"image_id": image_id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, response.content
    assert len(response.content) == 515

    # Boundary cases
    response = client.get(
        "/api/v1/bank/image/get",
        params={"image_id": 100},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 404, response.content
    assert response.json()["detail"]

    response = client.get(
        "/api/v1/bank/image/get",
        params={"image_id": "100"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 404, response.content

    response = client.get(
        "/api/v1/bank/image/get",
        params={"image_id": image_id},
    )
    assert response.status_code == 401, response.content

    # Unexpected cases
    response = client.get(
        "/api/v1/bank/image/get",
        params={"image_id": "this is not an integer"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 422, response.content

    response = client.post(
        "/api/v1/bank/image/get",
        params={"image_id": image_id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 405, response.content


def test_question_add(client, image_id, student_token, admin_token):
    """Test the question add endpoint

    Args:
        client (TestClient): the test client
        image_id (int): the ID of the uploaded image
        student_token (str): the student token
        admin_token (str): the admin token
    """
    # Expected cases
    question = {
        "source": "testing",
        "sub_questions": [
            {
                "description": "This is a test subquestion without image",
                "answer": "This is a standard answer to the subquestion",
                "concept": ConceptType.ELEMENTS_OF_CHANCE.value,
                "process": ProcessType.APPLY.value,
            },
            {
                "description": "This is test subquestion with image",
                "answer": "This is a standard answer to the subquestion",
                "concept": ConceptType.ELEMENTS_OF_CHANCE.value,
                "process": ProcessType.EXPLAIN.value,
                "image_id": image_id,
            },
        ],
    }
    response = client.post(
        "/api/v1/bank/question/add",
        json=question,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json()["question_id"]

    # Boundary cases
    response = client.post(
        "/api/v1/bank/question/add",
        json=question,
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, response.content

    # Unexpected cases
    response = client.post(
        "/api/v1/bank/question/add", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422, response.content

    response = client.get("/api/v1/bank/question/add")
    assert response.status_code == 405, response.content


def test_question_get(client, question_id, student_token, admin_token):
    """Test the question get endpoint

    Args:
        client (TestClient): the test client
        question_id (int): the ID of the uploaded question
        student_token (str): the student token
        admin_token (str): the admin token
    """
    # Expected cases
    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_id": question_id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json() == []  # Question is not audited so no result

    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_id": question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert len(response.json()) > 0, response.content
    assert response.json()[0]["id"] == question_id, response.content
    assert response.json()[0]["source"] == "testing", response.content

    response = client.get(
        "/api/v1/bank/question/get",
        params={"source": "not_testing"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json() == []

    response = client.get(
        "/api/v1/bank/question/get",
        params={"process": ProcessType.APPLY.value},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert len(response.json()) > 0, response.content

    response = client.get(
        "/api/v1/bank/question/get",
        params={"process": ProcessType.FORMULATE.value},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json() == []

    response = client.get(
        "/api/v1/bank/question/get",
        params={"concept": ConceptType.ELEMENTS_OF_CHANCE.value},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert len(response.json()) > 0, response.content

    response = client.get(
        "/api/v1/bank/question/get",
        params={"concept": ConceptType.MEASUREMENT.value},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json() == []

    # Boundary cases
    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_id": 100},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json() == []

    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_id": "100"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json() == []

    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_id": "this is not an integer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content

    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_id": question_id},
    )
    assert response.status_code == 401, response.content

    # Unexpected cases
    response = client.post(
        "/api/v1/bank/question/get",
        params={"question_id": question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 405, response.content


def test_question_approve(client, question_id, student_token, admin_token):
    """Test the question approve endpoint

    Args:
        client (TestClient): the test client
        question_id (int): the ID of the uploaded question
        student_token (str): the student token
        admin_token (str): the admin token
    """
    # Expected cases
    response = client.post(
        "/api/v1/bank/question/approve",
        json={"question_id": question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json()["msg"]

    # Boundary cases
    response = client.post(
        "/api/v1/bank/question/approve",
        json={"question_id": 100},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content

    response = client.post(
        "/api/v1/bank/question/approve",
        json={"question_id": "100"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content

    response = client.post(
        "/api/v1/bank/question/approve",
        json={"question_id": question_id},
    )
    assert response.status_code == 401, response.content

    response = client.post(
        "/api/v1/bank/question/approve",
        json={"question_id": "this is not an integer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content

    response = client.post(
        "/api/v1/bank/question/approve",
        json={"question_id": question_id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, response.content

    # Unexpected cases
    response = client.get(
        "/api/v1/bank/question/approve",
        params={"question_id": question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 405, response.content


def test_question_delete(client, question_id, student_token, admin_token):
    """Test the question delete endpoint

    Args:
        client (TestClient): the test client
        question_id (int): the ID of the uploaded question
        student_token (str): the student token
        admin_token (str): the admin token
    """
    # Expected cases
    response = client.delete(
        "/api/v1/bank/question/delete",
        params={"question_id": question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json()["msg"]

    # Boundary cases
    response = client.delete(
        "/api/v1/bank/question/delete",
        params={"question_id": 100},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content

    response = client.delete(
        "/api/v1/bank/question/delete",
        params={"question_id": "100"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content

    response = client.delete(
        "/api/v1/bank/question/delete",
        params={"question_id": "this is not an integer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content

    response = client.delete(
        "/api/v1/bank/question/delete",
        params={"question_id": question_id},
    )
    assert response.status_code == 401, response.content

    response = client.delete(
        "/api/v1/bank/question/delete",
        params={"question_id": question_id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, response.content

    # Unexpected cases
    response = client.get(
        "/api/v1/bank/question/delete",
        params={"question_id": question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 405, response.content
