import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from main import get_app

import backend.config as cfg
from backend.types.question import ConceptType, ProcessType


@pytest.fixture(scope="module")
def client():
    """Get a test HTTP client

    Returns:
        TestClient: A test client that has same methods of httpx.Client
    """
    app = get_app()
    return TestClient(app)


@pytest.fixture(scope="module")
def test_image_path():
    """Get the test image path

    Returns:
        Path: the path to the test image
    """
    return Path("src/tests/test_image.png")


@pytest.fixture(scope="module")
def uploaded_image_hash(client, test_image_path):
    """Upload a test image and return its hash

    Args:
        client (TestClient): the test client
        test_image_path (Path): the path to the test image

    Returns:
        str: the hash of the uploaded image
    """
    with open(test_image_path, "rb") as f:
        files = {"file": (test_image_path.name, f, "image/png")}
        response = client.post("/api/v1/bank/image/upload", files=files)
    assert response.status_code == 200
    return response.json()["hash"]


@pytest.fixture(scope="module")
def image_id(client, uploaded_image_hash):
    """Upload an image and return its ID

    Args:
        client (TestClient): the test client
        uploaded_image_hash (_type_): the hash of the uploaded image

    Returns:
        int: the ID of the uploaded image
    """
    response = client.post(
        "/api/v1/bank/image/add",
        json={"description": "A Test Image", "hash": uploaded_image_hash},
    )
    assert response.status_code == 200
    return response.json()["image_id"]


@pytest.fixture(scope="module")
def question_id(client, image_id):
    """Add a question and return its ID

    Args:
        client (TestClient): the test client
        image_id (int): the ID of the uploaded image

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
    response = client.post("/api/v1/bank/question/add", json=question)
    assert response.status_code == 200
    return response.json()["question_id"]


def test_image_upload(client, test_image_path):
    """Test the image upload endpoint

    Args:
        client (TestClient): the test client
        test_image_path (Path): the path to the test image
    """
    with open(test_image_path, "rb") as f:
        files = {"file": (test_image_path.name, f, "image/png")}
        response = client.post("/api/v1/bank/image/upload", files=files)
    assert response.status_code == 200
    assert response.json()["hash"]
    assert (
        cfg.config.image_store_path / "95d17bdeaca5d43432576b71043ef9f8.png"
    ).exists()

    with open(test_image_path, "rb") as f:
        files = {"file": (test_image_path.name, f, "image/gif")}
        response = client.post("/api/v1/bank/image/upload", files=files)
    assert response.status_code == 400
    assert "unsupported content_type" in response.json()["detail"].lower()

    response = client.post("/api/v1/bank/image/upload")
    assert response.status_code == 422


def test_image_add(client, uploaded_image_hash):
    """Test the image add endpoint

    Args:
        client (TestClient): the test client
        uploaded_image_hash (str): the hash of the uploaded image
    """
    response = client.post(
        "/api/v1/bank/image/add",
        json={"description": "A Test Image", "hash": uploaded_image_hash},
    )
    assert response.status_code == 200
    assert response.json()["image_id"]

    response = client.post(
        "/api/v1/bank/image/add",
        json={"description": "Unexist image", "hash": "1" * 32},
    )
    assert response.status_code == 404
    assert response.json()["detail"]

    response = client.post("/api/v1/bank/image/add")
    assert response.status_code == 422


def test_image_get(client, image_id):
    """Test the image get endpoint

    Args:
        client (TestClient): the test client
        image_id (int): the ID of the uploaded image
    """
    response = client.get("/api/v1/bank/image/get", params={"image_id": image_id})
    assert response.status_code == 200
    assert len(response.content) == 515

    response = client.get("/api/v1/bank/image/get", params={"image_id": 100})
    assert response.status_code == 404
    assert response.json()["detail"]

    response = client.get("/api/v1/bank/image/get", params={"image_id": "100"})
    assert response.status_code == 404

    response = client.get(
        "/api/v1/bank/image/get", params={"image_id": "this is not an integer"}
    )
    assert response.status_code == 422


def test_question_add(client, image_id):
    """Test the question add endpoint

    Args:
        client (TestClient): the test client
        image_id (int): the ID of the uploaded image
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
    response = client.post("/api/v1/bank/question/add", json=question)
    assert response.status_code == 200
    assert response.json()["question_id"]

    response = client.post("/api/v1/bank/question/add")
    assert response.status_code == 422


def test_question_get(client, question_id):
    """Test the question get endpoint

    Args:
        client (TestClient): the test client
        question_id (int): the ID of the uploaded question
    """
    response = client.get(
        "/api/v1/bank/question/get", params={"question_id": question_id}
    )
    assert response.status_code == 200
    assert response.json() == []  # Question is not audited so no result

    response = client.get("/api/v1/bank/question/get", params={"question_id": 100})
    assert response.status_code == 200
    assert response.json() == []

    # TODO: Different authorisations with different responses

    response = client.get("/api/v1/bank/question/get", params={"question_id": "100"})
    assert response.status_code == 200
    assert response.json() == []

    response = client.get(
        "/api/v1/bank/question/get", params={"question_id": "this is not an integer"}
    )
    assert response.status_code == 422


def test_question_approve(client, question_id):
    """Test the question approve endpoint

    Args:
        client (TestClient): the test client
        question_id (int): the ID of the uploaded question
    """
    response = client.get(
        "/api/v1/bank/question/approve", params={"question_id": question_id}
    )
    assert response.status_code == 200
    assert response.json()["msg"]

    response = client.get("/api/v1/bank/question/approve", params={"question_id": 100})
    assert response.status_code == 422
    assert "invalid" in response.json()["detail"].lower()

    response = client.get(
        "/api/v1/bank/question/approve", params={"question_id": "100"}
    )
    assert response.status_code == 422
    assert "invalid" in response.json()["detail"].lower()

    response = client.get(
        "/api/v1/bank/question/approve",
        params={"question_id": "this is not an integer"},
    )
    assert response.status_code == 422


def test_question_delete(client, question_id):
    """Test the question delete endpoint

    Args:
        client (TestClient): the test client
        question_id (int): the ID of the uploaded question
    """
    response = client.delete(
        "/api/v1/bank/question/delete", params={"question_id": question_id}
    )
    assert response.status_code == 200
    assert response.json()["msg"]

    response = client.delete(
        "/api/v1/bank/question/delete", params={"question_id": 100}
    )
    assert response.status_code == 422
    assert "invalid" in response.json()["detail"].lower()

    response = client.delete(
        "/api/v1/bank/question/delete", params={"question_id": "100"}
    )
    assert response.status_code == 422
    assert "invalid" in response.json()["detail"].lower()

    response = client.delete(
        "/api/v1/bank/question/delete", params={"question_id": "this is not an integer"}
    )
    assert response.status_code == 422
