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
def test_image2_path():
    """Get the test image path

    Returns:
        Path: the path to the test image
    """
    return Path("src/tests/test_image2.png")


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
def uploaded_image2_hash(client, test_image2_path, admin_token):
    """Upload a test image and return its hash

    Args:
        client (TestClient): the test client
        test_image2_path (Path): the path to the test image
        admin_token (str): the admin token

    Returns:
        str: the hash of the uploaded image
    """
    with open(test_image2_path, "rb") as f:
        files = {"file": (test_image2_path.name, f, "image/png")}
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
        "name": "Test Question",
        "source": "testing",
        "sub_questions": [
            {
                "description": "This is a test subquestion without image",
                "answer": "This is a standard answer to the subquestion",
                "concept": ConceptType.ELEMENTS_OF_CHANCE.value,
                "process": ProcessType.APPLY.value,
                "options": ["option1", "option2"],
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


@pytest.fixture(scope="module")
def sub_question_id(client, question_id, admin_token):
    """Get the ID of a sub-question

    Args:
        client (TestClient): the test client
        question_id (int): the ID of the question
        admin_token (str): the admin token

    Returns:
        int: the ID of the sub-question
    """
    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_ids": [question_id]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert len(response.json()) > 0, response.content
    assert len(response.json()[0]["sub_questions"]) > 0, response.content
    return response.json()[0]["sub_questions"][0]["id"]


@pytest.fixture(scope="module")
def question_id2(client, image_id, admin_token):
    """Add a second question and return its ID

    Args:
        client (TestClient): the test client
        image_id (int): the ID of the uploaded image
        admin_token (str): the admin token

    Returns:
        int: the ID of the added question
    """
    question = {
        "name": "Test Question 2",
        "source": "testing2",
        "sub_questions": [
            {
                "description": "This is a second test subquestion",
                "answer": "This is the answer to the second subquestion",
                "concept": ConceptType.MEASUREMENT.value,
                "process": ProcessType.FORMULATE.value,
                "options": ["option_a", "option_b"],
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

    response = client.get(
        "/api/v1/bank/image/get",
        params={"image_id": image_id},
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
        "name": "Test Question",
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


def test_question_get(client, question_id, question_id2, student_token, admin_token):
    """Test the question get endpoint

    Args:
        client (TestClient): the test client
        question_id (int): the ID of the first uploaded question
        question_id2 (int): the ID of the second uploaded question
        student_token (str): the student token
        admin_token (str): the admin token
    """
    # Expected cases
    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_ids": [question_id]},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json() == []  # Question is not audited so no result

    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_ids": [question_id]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert len(response.json()) > 0, response.content
    assert response.json()[0]["id"] == question_id, response.content
    assert response.json()[0]["name"] == "Test Question", response.content
    assert response.json()[0]["source"] == "testing", response.content

    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_ids": [question_id, question_id2]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert len(response.json()) == 2, response.content
    question_ids_returned = [q["id"] for q in response.json()]
    assert question_id in question_ids_returned, response.content
    assert question_id2 in question_ids_returned, response.content

    response = client.get(
        "/api/v1/bank/question/get",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content

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
    assert len(response.json()) > 0, response.content

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
    assert len(response.json()) > 0, response.content

    response = client.get(
        "/api/v1/bank/question/get",
        params={"keyword": "Test Question"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert len(response.json()) > 0, response.content

    response = client.get(
        "/api/v1/bank/question/get",
        params={"keyword": "Non-existent Question"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json() == []

    # Boundary cases
    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_ids": [100]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json() == []

    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_ids": [100, 200]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json() == []

    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_ids": [question_id, 100]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert len(response.json()) == 1, response.content
    assert response.json()[0]["id"] == question_id, response.content

    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_ids": ["not_an_integer"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content

    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_ids": [question_id]},
    )
    assert response.status_code == 401, response.content

    # Unexpected cases
    response = client.post(
        "/api/v1/bank/question/get",
        params={"question_ids": [question_id]},
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


def test_image_set_description(client, image_id, student_token, admin_token):
    """Test the image set description endpoint

    Args:
        client (TestClient): the test client
        image_id (int): the ID of the uploaded image
        student_token (str): the student token
        admin_token (str): the admin token
    """
    # Expected cases
    response = client.post(
        "/api/v1/bank/image/set/description",
        json={"image_id": image_id, "description": "Updated description"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json()["msg"] == f"Set description of image {image_id}"

    # Boundary cases
    response = client.post(
        "/api/v1/bank/image/set/description",
        json={"image_id": 100, "description": "Updated description"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content
    assert "No image with id 100 found" in response.json()["detail"]

    response = client.post(
        "/api/v1/bank/image/set/description",
        json={"image_id": image_id, "description": "Updated description"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, response.content

    response = client.post(
        "/api/v1/bank/image/set/description",
        json={"image_id": image_id, "description": "Updated description"},
    )
    assert response.status_code == 401, response.content

    # Unexpected cases
    response = client.post(
        "/api/v1/bank/image/set/description",
        json={
            "image_id": "this is not an integer",
            "description": "Updated description",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content

    response = client.post(
        "/api/v1/bank/image/set/description",
        json={"image_id": image_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content


def test_image_set_hash(
    client, image_id, uploaded_image2_hash, student_token, admin_token
):
    """Test the image set hash endpoint

    Args:
        client (TestClient): the test client
        image_id (int): the ID of the uploaded image
        uploaded_image_hash (str): the hash of the uploaded image
        student_token (str): the student token
        admin_token (str): the admin token
    """
    # Expected cases
    response = client.post(
        "/api/v1/bank/image/set/hash",
        json={"image_id": image_id, "hash": uploaded_image2_hash},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json()["msg"] == f"Set hash of image {image_id}"

    # Boundary cases
    response = client.post(
        "/api/v1/bank/image/set/hash",
        json={"image_id": 100, "hash": uploaded_image2_hash},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content
    assert "No image with id 100 found" in response.json()["detail"]

    response = client.post(
        "/api/v1/bank/image/set/hash",
        json={"image_id": image_id, "hash": "invalid_hash"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content
    assert "No image with hash invalid_hash found" in response.json()["detail"]

    response = client.post(
        "/api/v1/bank/image/set/hash",
        json={"image_id": image_id, "hash": uploaded_image2_hash},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, response.content

    response = client.post(
        "/api/v1/bank/image/set/hash",
        json={"image_id": image_id, "hash": uploaded_image2_hash},
    )
    assert response.status_code == 401, response.content

    # Unexpected cases
    response = client.post(
        "/api/v1/bank/image/set/hash",
        json={"image_id": "this is not an integer", "hash": uploaded_image2_hash},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content

    response = client.post(
        "/api/v1/bank/image/set/hash",
        json={"image_id": image_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content


def test_sub_question_set_description(
    client, sub_question_id, student_token, admin_token
):
    """Test the sub-question set description endpoint

    Args:
        client (TestClient): the test client
        sub_question_id (int): the ID of the sub-question
        student_token (str): the student token
        admin_token (str): the admin token
    """
    # Expected cases
    response = client.post(
        "/api/v1/bank/sub-question/set/description",
        json={"sub_question_id": sub_question_id, "description": "Updated description"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert (
        response.json()["msg"] == f"Set description of sub-question {sub_question_id}"
    )

    # Boundary cases
    response = client.post(
        "/api/v1/bank/sub-question/set/description",
        json={"sub_question_id": 100, "description": "Updated description"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content
    assert "No sub-question with id 100 found" in response.json()["detail"]

    response = client.post(
        "/api/v1/bank/sub-question/set/description",
        json={"sub_question_id": sub_question_id, "description": "Updated description"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, response.content

    response = client.post(
        "/api/v1/bank/sub-question/set/description",
        json={"sub_question_id": sub_question_id, "description": "Updated description"},
    )
    assert response.status_code == 401, response.content

    # Unexpected cases
    response = client.post(
        "/api/v1/bank/sub-question/set/description",
        json={
            "sub_question_id": "this is not an integer",
            "description": "Updated description",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content

    response = client.post(
        "/api/v1/bank/sub-question/set/description",
        json={"sub_question_id": sub_question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content


def test_sub_question_set_options(client, sub_question_id, student_token, admin_token):
    """Test the sub-question set options endpoint

    Args:
        client (TestClient): the test client
        sub_question_id (int): the ID of the sub-question
        student_token (str): the student token
        admin_token (str): the admin token
    """
    # Expected cases
    response = client.post(
        "/api/v1/bank/sub-question/set/options",
        json={"sub_question_id": sub_question_id, "options": ["Option 1", "Option 2"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json()["msg"] == f"Set options of sub-question {sub_question_id}"

    # Boundary cases
    response = client.post(
        "/api/v1/bank/sub-question/set/options",
        json={"sub_question_id": 100, "options": ["Option 1", "Option 2"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content
    assert "No sub-question with id 100 found" in response.json()["detail"]

    response = client.post(
        "/api/v1/bank/sub-question/set/options",
        json={"sub_question_id": sub_question_id, "options": ["Option 1", "Option 2"]},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, response.content

    response = client.post(
        "/api/v1/bank/sub-question/set/options",
        json={"sub_question_id": sub_question_id, "options": ["Option 1", "Option 2"]},
    )
    assert response.status_code == 401, response.content

    # Unexpected cases
    response = client.post(
        "/api/v1/bank/sub-question/set/options",
        json={
            "sub_question_id": "this is not an integer",
            "options": ["Option 1", "Option 2"],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content

    response = client.post(
        "/api/v1/bank/sub-question/set/options",
        json={"sub_question_id": sub_question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content


def test_sub_question_set_answer(client, sub_question_id, student_token, admin_token):
    """Test the sub-question set answer endpoint

    Args:
        client (TestClient): the test client
        sub_question_id (int): the ID of the sub-question
        student_token (str): the student token
        admin_token (str): the admin token
    """
    # Expected cases
    response = client.post(
        "/api/v1/bank/sub-question/set/answer",
        json={"sub_question_id": sub_question_id, "answer": "Updated answer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json()["msg"] == f"Set answer of sub-question {sub_question_id}"

    # Boundary cases
    response = client.post(
        "/api/v1/bank/sub-question/set/answer",
        json={"sub_question_id": 100, "answer": "Updated answer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content
    assert "No sub-question with id 100 found" in response.json()["detail"]

    response = client.post(
        "/api/v1/bank/sub-question/set/answer",
        json={"sub_question_id": sub_question_id, "answer": "Updated answer"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, response.content

    response = client.post(
        "/api/v1/bank/sub-question/set/answer",
        json={"sub_question_id": sub_question_id, "answer": "Updated answer"},
    )
    assert response.status_code == 401, response.content

    # Unexpected cases
    response = client.post(
        "/api/v1/bank/sub-question/set/answer",
        json={"sub_question_id": "this is not an integer", "answer": "Updated answer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content

    response = client.post(
        "/api/v1/bank/sub-question/set/answer",
        json={"sub_question_id": sub_question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content


def test_sub_question_set_concept(client, sub_question_id, student_token, admin_token):
    """Test the sub-question set concept endpoint

    Args:
        client (TestClient): the test client
        sub_question_id (int): the ID of the sub-question
        student_token (str): the student token
        admin_token (str): the admin token
    """
    # Expected cases
    response = client.post(
        "/api/v1/bank/sub-question/set/concept",
        json={
            "sub_question_id": sub_question_id,
            "concept": ConceptType.MEASUREMENT.value,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json()["msg"] == f"Set concept of sub-question {sub_question_id}"

    # Boundary cases
    response = client.post(
        "/api/v1/bank/sub-question/set/concept",
        json={"sub_question_id": 100, "concept": ConceptType.MEASUREMENT.value},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content
    assert "No sub-question with id 100 found" in response.json()["detail"]

    response = client.post(
        "/api/v1/bank/sub-question/set/concept",
        json={
            "sub_question_id": sub_question_id,
            "concept": ConceptType.MEASUREMENT.value,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, response.content

    response = client.post(
        "/api/v1/bank/sub-question/set/concept",
        json={
            "sub_question_id": sub_question_id,
            "concept": ConceptType.MEASUREMENT.value,
        },
    )
    assert response.status_code == 401, response.content

    # Unexpected cases
    response = client.post(
        "/api/v1/bank/sub-question/set/concept",
        json={
            "sub_question_id": "this is not an integer",
            "concept": ConceptType.MEASUREMENT.value,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content

    response = client.post(
        "/api/v1/bank/sub-question/set/concept",
        json={"sub_question_id": sub_question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content


def test_sub_question_set_process(client, sub_question_id, student_token, admin_token):
    """Test the sub-question set process endpoint

    Args:
        client (TestClient): the test client
        sub_question_id (int): the ID of the sub-question
        student_token (str): the student token
        admin_token (str): the admin token
    """
    # Expected cases
    response = client.post(
        "/api/v1/bank/sub-question/set/process",
        json={
            "sub_question_id": sub_question_id,
            "process": ProcessType.FORMULATE.value,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json()["msg"] == f"Set process of sub-question {sub_question_id}"

    # Boundary cases
    response = client.post(
        "/api/v1/bank/sub-question/set/process",
        json={"sub_question_id": 100, "process": ProcessType.FORMULATE.value},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content
    assert "No sub-question with id 100 found" in response.json()["detail"]

    response = client.post(
        "/api/v1/bank/sub-question/set/process",
        json={
            "sub_question_id": sub_question_id,
            "process": ProcessType.FORMULATE.value,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, response.content

    response = client.post(
        "/api/v1/bank/sub-question/set/process",
        json={
            "sub_question_id": sub_question_id,
            "process": ProcessType.FORMULATE.value,
        },
    )
    assert response.status_code == 401, response.content

    # Unexpected cases
    response = client.post(
        "/api/v1/bank/sub-question/set/process",
        json={
            "sub_question_id": "this is not an integer",
            "process": ProcessType.FORMULATE.value,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content

    response = client.post(
        "/api/v1/bank/sub-question/set/process",
        json={"sub_question_id": sub_question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content


def test_sub_question_set_keywords(client, sub_question_id, student_token, admin_token):
    """Test the sub-question set keywords endpoint

    Args:
        client (TestClient): the test client
        sub_question_id (int): the ID of the sub-question
        student_token (str): the student token
        admin_token (str): the admin token
    """
    # Expected cases
    response = client.post(
        "/api/v1/bank/sub-question/set/keywords",
        json={
            "sub_question_id": sub_question_id,
            "keywords": ["Keyword 1", "Keyword 2"],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json()["msg"] == f"Set keywords of sub-question {sub_question_id}"

    # Boundary cases
    response = client.post(
        "/api/v1/bank/sub-question/set/keywords",
        json={"sub_question_id": 100, "keywords": ["Keyword 1", "Keyword 2"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content
    assert "No sub-question with id 100 found" in response.json()["detail"]

    response = client.post(
        "/api/v1/bank/sub-question/set/keywords",
        json={
            "sub_question_id": sub_question_id,
            "keywords": ["Keyword 1", "Keyword 2"],
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, response.content

    response = client.post(
        "/api/v1/bank/sub-question/set/keywords",
        json={
            "sub_question_id": sub_question_id,
            "keywords": ["Keyword 1", "Keyword 2"],
        },
    )
    assert response.status_code == 401, response.content

    # Unexpected cases
    response = client.post(
        "/api/v1/bank/sub-question/set/keywords",
        json={
            "sub_question_id": "this is not an integer",
            "keywords": ["Keyword 1", "Keyword 2"],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content

    response = client.post(
        "/api/v1/bank/sub-question/set/keywords",
        json={"sub_question_id": sub_question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content


def test_sub_question_set_image(
    client, sub_question_id, image_id, student_token, admin_token
):
    """Test the sub-question set image endpoint

    Args:
        client (TestClient): the test client
        sub_question_id (int): the ID of the sub-question
        image_id (int): the ID of the image
        student_token (str): the student token
        admin_token (str): the admin token
    """
    # Expected cases
    response = client.post(
        "/api/v1/bank/sub-question/set/image",
        json={"sub_question_id": sub_question_id, "image_id": image_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json()["msg"] == f"Set image of sub-question {sub_question_id}"

    # Boundary cases
    response = client.post(
        "/api/v1/bank/sub-question/set/image",
        json={"sub_question_id": 100, "image_id": image_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content
    assert "No sub-question with id 100 found" in response.json()["detail"]

    response = client.post(
        "/api/v1/bank/sub-question/set/image",
        json={"sub_question_id": sub_question_id, "image_id": 100},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content
    assert "No image with id 100 found" in response.json()["detail"]

    response = client.post(
        "/api/v1/bank/sub-question/set/image",
        json={"sub_question_id": sub_question_id, "image_id": image_id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, response.content

    response = client.post(
        "/api/v1/bank/sub-question/set/image",
        json={"sub_question_id": sub_question_id, "image_id": image_id},
    )
    assert response.status_code == 401, response.content

    # Unexpected cases
    response = client.post(
        "/api/v1/bank/sub-question/set/image",
        json={"sub_question_id": "this is not an integer", "image_id": image_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content

    response = client.post(
        "/api/v1/bank/sub-question/set/image",
        json={"sub_question_id": sub_question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content


def test_question_set_name(client, question_id, student_token, admin_token):
    """Test the question set name endpoint

    Args:
        client (TestClient): the test client
        question_id (int): the ID of the question
        student_token (str): the student token
        admin_token (str): the admin token
    """
    # Expected cases
    response = client.post(
        "/api/v1/bank/question/set/name",
        json={"question_id": question_id, "name": "Updated Test Question"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.content
    assert response.json()["msg"] == f"Set name of question {question_id}"

    # Boundary cases
    response = client.post(
        "/api/v1/bank/question/set/name",
        json={"question_id": 100, "name": "Updated Test Question"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, response.content
    assert "No question with id 100 found" in response.json()["detail"]

    response = client.post(
        "/api/v1/bank/question/set/name",
        json={"question_id": question_id, "name": "Updated Test Question"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, response.content

    response = client.post(
        "/api/v1/bank/question/set/name",
        json={"question_id": question_id, "name": "Updated Test Question"},
    )
    assert response.status_code == 401, response.content

    # Unexpected cases
    response = client.post(
        "/api/v1/bank/question/set/name",
        json={"question_id": "this is not an integer", "name": "Updated Test Question"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content

    response = client.post(
        "/api/v1/bank/question/set/name",
        json={"question_id": question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422, response.content
