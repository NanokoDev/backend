import pytest

import backend.config as cfg
from backend.types.user import Permission

from .resources import llm_api_callback


user_question_id_cache = None
user_sub_question_id_cache = None
class_id_cache = None
class_name_cache = None
assignment_id_cache = None


@pytest.fixture(scope="module")
def question_id(client, admin_token):
    """Get a sub question id, if not exist, create one

    Args:
        client (TestClient): The test client
        admin_token (str): The admin token
    """
    global user_question_id_cache
    if user_question_id_cache is not None:
        return user_question_id_cache
    question = {
        "name": "User Test Question",
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
    user_question_id_cache = question_id

    # approve the question
    response = client.post(
        "/api/v1/bank/question/approve",
        json={"question_id": question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to approve question: {response.content}"
    )

    return user_question_id_cache


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
    global user_sub_question_id_cache
    if user_sub_question_id_cache is not None:
        return user_sub_question_id_cache
    response = client.get(
        "/api/v1/bank/question/get",
        params={"question_ids": [question_id]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, f"Failed to get question: {response.content}"
    sub_question_id = response.json()[0]["sub_questions"][0]["id"]
    user_sub_question_id_cache = sub_question_id
    return user_sub_question_id_cache


@pytest.fixture(scope="module")
def class_id(client, teacher_token):
    """Get a class id, if not exist, create one

    Args:
        client (TestClient): The test client
        teacher_token (str): The teacher token
    """
    global class_id_cache, class_name_cache
    if class_id_cache is not None:
        return class_id_cache
    response = client.post(
        "/api/v1/user/class/create",
        json={
            "class_name": "Test Class",
            "enter_code": "test_code",
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 200, f"Failed to create class: {response.content}"
    class_id = response.json()["id"]
    class_name_cache = response.json()["name"]
    class_id_cache = class_id
    return class_id_cache


@pytest.fixture(scope="module")
def assignment_id(client, teacher_token, question_id, class_id):
    """Get an assignment id, if not exist, create one

    Args:
        client (TestClient): The test client
        teacher_token (str): The teacher token
        question_id (int): The question id
        class_id (int): The class id
    """
    global assignment_id_cache
    if assignment_id_cache is not None:
        return assignment_id_cache

    class_id = class_id  # Ensure the teacher is teaching a class

    response = client.post(
        "/api/v1/user/assignment/create",
        json={
            "assignment_name": "Test Assignment",
            "description": "This is a test assignment",
            "question_ids": [question_id],
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to create assignment: {response.content}"
    )
    assignment_id = response.json()["id"]
    assignment_id_cache = assignment_id
    return assignment_id_cache


def test_me(client, admin_token, student_token, teacher_token):
    """Test the /api/v1/user/me endpoint

    Args:
        client (TestClient): The test client
        admin_token (str): The admin token
        student_token (str): The student token
        teacher_token (str): The teacher token
    """
    # Expected cases
    response = client.get(
        "/api/v1/user/me", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200, f"Failed to get admin user: {response.content}"
    assert response.json()["name"] == cfg.config.admin_username
    assert response.json()["permission"] == Permission.ADMIN.value
    assert response.json()["email"] == cfg.config.admin_email
    assert response.json()["display_name"] == cfg.config.admin_display_name

    response = client.get(
        "/api/v1/user/me", headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 200, (
        f"Failed to get student user: {response.content}"
    )
    assert response.json()["name"] == "student"
    assert response.json()["permission"] == Permission.STUDENT.value
    assert response.json()["email"] == "student_email@example.com"
    assert response.json()["display_name"] == "Student"

    response = client.get(
        "/api/v1/user/me", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200, (
        f"Failed to get teacher user: {response.content}"
    )
    assert response.json()["name"] == "teacher"
    assert response.json()["permission"] == Permission.TEACHER.value
    assert response.json()["email"] == "teacher_email@example.com"
    assert response.json()["display_name"] == "Teacher"

    # Boundary cases
    response = client.get(
        "/api/v1/user/me", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401, (
        f"Failed to 401 unauthorised: {response.content}"
    )
    assert response.headers["WWW-Authenticate"] == "Bearer"

    # Unexpected cases
    response = client.get("/api/v1/user/me")
    assert response.status_code == 401, (
        f"Failed to 401 unauthorised: {response.content}"
    )
    assert response.headers["WWW-Authenticate"] == "Bearer"

    response = client.post(
        "/api/v1/user/me", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 405, (
        f"Failed to 405 method not allowed: {response.content}"
    )


def test_register(client):
    """Test the /api/v1/user/register endpoint

    Args:
        client (TestClient): The test client
    """
    # Expected cases
    response = client.post(
        "/api/v1/user/register",
        json={
            "username": "new_student",
            "email": "random_email@example.com",
            "display_name": "New Student",
            "password": "new_student_password",
            "permission": Permission.STUDENT.value,
        },
    )
    assert response.status_code == 200, (
        f"Failed to register new student: {response.content}"
    )
    assert response.json()["name"] == "new_student"
    assert response.json()["permission"] == Permission.STUDENT.value
    assert response.json()["email"] == "random_email@example.com"
    assert response.json()["display_name"] == "New Student"

    response = client.post(
        "/api/v1/user/register",
        json={
            "username": "new_teacher",
            "email": "random_email2@example.com",
            "display_name": "New Teacher",
            "password": "new_teacher_password",
            "permission": Permission.TEACHER.value,
        },
    )
    assert response.status_code == 200, (
        f"Failed to register new teacher: {response.content}"
    )
    assert response.json()["name"] == "new_teacher"
    assert response.json()["permission"] == Permission.TEACHER.value
    assert response.json()["email"] == "random_email2@example.com"
    assert response.json()["display_name"] == "New Teacher"

    # Boundary cases
    response = client.post(
        "/api/v1/user/register",
        json={
            "username": "new_student2",
            "email": "not_a_valid_email",  # Invalid email format
            "display_name": "New Student",
            "password": "new_student_password",
            "permission": Permission.STUDENT.value,
        },
    )
    assert response.status_code == 400, (
        f"Failed to get 400 bad request: {response.content}"
    )

    response = client.post(
        "/api/v1/user/register",
        json={
            "username": "new_student",  # Duplicate username
            "email": "122@example.com",
            "display_name": "New Student",
            "password": "new_student_password",
            "permission": Permission.STUDENT.value,
        },
    )
    assert response.status_code == 400, (
        f"Failed to get 400 bad request: {response.content}"
    )

    response = client.post(
        "/api/v1/user/register",
        json={
            "username": "new_student3",
            "email": "random_email@example.com",  # Duplicate email
            "display_name": "New Student",
            "password": "new_student_password",
            "permission": Permission.STUDENT.value,
        },
    )
    assert response.status_code == 400, (
        f"Failed to get 400 bad request: {response.content}"
    )

    # Unexpected cases
    response = client.post(
        "/api/v1/user/register",
        json={
            "username": "new_admin",
            "email": "111@example.com",
            "display_name": "New Admin",
            "password": "new_admin_password",
            "permission": Permission.ADMIN.value,
        },
    )
    assert response.status_code == 403, (
        f"Failed to get 403 forbidden: {response.content}"
    )

    response = client.get(
        "/api/v1/user/register",
        params={
            "username": "new_student123",
            "email": "1@1.1",
            "display_name": "New Student",
            "password": "new_student_password",
            "permission": Permission.STUDENT.value,
        },
    )
    assert response.status_code == 405, (
        f"Failed to get 405 method not allowed: {response.content}"
    )

    response = client.post(
        "/api/v1/user/register",
        json={
            "username": "new_student1223",
            "display_name": "New Student",
            "password": "new_student_password",
            "permission": Permission.STUDENT.value,
        },  # Missing email field
    )
    assert response.status_code == 422, (
        f"Failed to get 422 unprocessable entity: {response.content}"
    )


def test_create_class(client, teacher_token, student_token):
    """Test the /api/v1/user/class/create endpoint

    Args:
        client (TestClient): The test client
        teacher_token (str): The teacher token
        student_token (str): The student token
    """
    # Expected cases
    global class_id_cache, class_name_cache
    if class_id_cache is None:
        response = client.post(
            "/api/v1/user/class/create",
            json={
                "class_name": "Test Class",
                "enter_code": "test_code",
            },
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert response.status_code == 200, (
            f"Failed to create class: {response.content}"
        )
        class_name_cache = response.json()["name"]
        class_id_cache = response.json()["id"]
    # If class_id_cache is not None, it is promised that class can be created successfully

    # Boundary cases
    response = client.post(
        "/api/v1/user/class/create",
        json={
            "class_name": "Test Class2",
            "enter_code": "test_code",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, (
        f"Failed to get 403 forbidden: {response.content}"
    )

    response = client.post(
        "/api/v1/user/class/create",
        json={
            "class_name": "Test Class",  # Duplicate class name
            "enter_code": "test_code",
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 400, (
        f"Failed to get 400 bad request: {response.content}"
    )

    # Unexpected cases
    response = client.get(
        "/api/v1/user/class/create",
        headers={"Authorization": f"Bearer {teacher_token}"},
        params={
            "class_name": "Test Clas2s",
            "enter_code": "test_code",
        },
    )
    assert response.status_code == 405, (
        f"Failed to get 405 method not allowed: {response.content}"
    )


def test_create_assignment(client, teacher_token, student_token, question_id):
    """Test the /api/v1/user/assignment/create endpoint

    Args:
        client (TestClient): The test client
        student_token (str): The student token
        teacher_token (str): The teacher token
        question_id (int): The question id
    """
    # Expected cases
    global assignment_id_cache
    if assignment_id_cache is None:
        response = client.post(
            "/api/v1/user/assignment/create",
            json={
                "assignment_name": "Test Assignment",
                "description": "This is a test assignment",
                "question_ids": [question_id],
            },
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert response.status_code == 200, (
            f"Failed to create assignment: {response.content}"
        )
        assignment_id = response.json()["id"]
        assignment_id_cache = assignment_id

    # Boundary cases
    response = client.post(
        "/api/v1/user/assignment/create",
        json={
            "assignment_name": "Test Assignment2",
            "description": "This is a test assignment",
            "question_ids": [question_id],
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, (
        f"Failed to get 403 forbidden: {response.content}"
    )

    # Unexpected cases
    response = client.get(
        "/api/v1/user/assignment/create",
        headers={"Authorization": f"Bearer {teacher_token}"},
        params={
            "assignment_name": "Test Assignment2",
            "description": "This is a test assignment",
            "question_ids": [question_id],
        },
    )
    assert response.status_code == 405, (
        f"Failed to get 405 method not allowed: {response.content}"
    )

    response = client.post(
        "/api/v1/user/assignment/create",
        json={
            "assignment_name": "Test Assignment2",
            "description": "This is a test assignment",
            # Missing question_ids field
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 422, (
        f"Failed to get 422 unprocessable entity: {response.content}"
    )


def test_join_class(client, student_token, teacher_token, admin_token, class_id):
    """Test the /api/v1/user/class/join endpoint

    Args:
        client (TestClient): The test client
        student_token (str): The student token
        teacher_token (str): The teacher token
        admin_token (str): The admin token
        class_id (int): The class id
    """
    class_id = class_id
    # Ensure the class is created, and so the class_name_cache is not None

    global class_name_cache
    assert class_name_cache is not None, "Class name cache is None"

    # Expected cases
    response = client.post(
        "/api/v1/user/class/join",
        json={"enter_code": "test_code", "class_name": class_name_cache},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, f"Failed to join class: {response.content}"

    # Boundary cases
    response = client.post(
        "/api/v1/user/class/join",
        json={"enter_code": "test_code", "class_name": class_name_cache},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 403, (
        f"Failed to get 403 bad request: {response.content}"
    )

    response = client.post(
        "/api/v1/user/class/join",
        json={
            "enter_code": "test_code",
            "class_name": "Test Class2",
        },  # invalid class name
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 404, (
        f"Failed to get 404 not found: {response.content}"
    )

    response = client.post(
        "/api/v1/user/class/join",
        json={
            "enter_code": "wrong_code",  # incorrect enter code
            "class_name": class_name_cache,
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        },  # use admin because the student is already in the class
    )
    assert response.status_code == 404, (
        f"Failed to get 404 not found: {response.content}"
    )

    # Unexpected cases
    response = client.get(
        "/api/v1/user/class/join",
        headers={"Authorization": f"Bearer {student_token}"},
        params={"enter_code": "test_code"},
    )
    assert response.status_code == 405, (
        f"Failed to get 405 method not allowed: {response.content}"
    )


def test_assign_assignment(
    client, teacher_token, student_token, assignment_id, class_id
):
    """Test the /api/v1/user/assignment/assign endpoint

    Args:
        client (TestClient): The test client
        teacher_token (str): The teacher token
        student_token (str): The student token
        assignment_id (int): The assignment id
        class_id (int): The class id
    """
    # Expected cases
    response = client.post(
        "/api/v1/user/assignment/assign",
        json={
            "assignment_id": assignment_id,
            "class_id": class_id,
            "due_date": "2077-05-31T23:40:03.266Z",
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to assign assignment: {response.content}"
    )

    # Boundary cases
    response = client.post(
        "/api/v1/user/assignment/assign",
        json={
            "assignment_id": assignment_id,
            "class_id": class_id,
            "due_date": "2077-05-31T23:40:03.266Z",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, (
        f"Failed to get 403 forbidden: {response.content}"
    )

    response = client.post(
        "/api/v1/user/assignment/assign",
        json={
            "assignment_id": assignment_id,
            "class_id": 99999999,  # Invalid class id
            "due_date": "2077-05-31T23:40:03.266Z",
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 404, (
        f"Failed to get 404 not found: {response.content}"
    )

    response = client.post(
        "/api/v1/user/assignment/assign",
        json={
            "assignment_id": 99999999,  # Invalid assignment id
            "class_id": class_id,
            "due_date": "2077-05-31T23:40:03.266Z",
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 404, (
        f"Failed to get 404 not found: {response.content}"
    )

    # Unexpected cases
    response = client.get(
        "/api/v1/user/assignment/assign",
        headers={"Authorization": f"Bearer {teacher_token}"},
        params={
            "assignment_id": assignment_id,
            "class_id": class_id,
            "due_date": "2077-05-31T23:40:03.266Z",
        },
    )
    assert response.status_code == 405, (
        f"Failed to get 405 method not allowed: {response.content}"
    )

    response = client.post(
        "/api/v1/user/assignment/assign",
        json={
            "class_id": class_id,
            "due_date": "2077-05-31T23:40:03.266Z",
            # missing assignment_id field
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 422, (
        f"Failed to get 422 unprocessable entity: {response.content}"
    )


def test_get_assignments(
    client, student_token, teacher_token, admin_token, assignment_id
):
    """Test the /api/v1/user/assignments endpoint

    Args:
        client (TestClient): The test client
        student_token (str): The student token
        teacher_token (str): The teacher token
        admin_token (str): The admin token
        assignment_id (int): The assignment id
    """
    # Expected cases
    response = client.get(
        "/api/v1/user/assignments",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, f"Failed to get assignment: {response.content}"
    assert len(response.json()) == 1, (
        f"Failed to get the correct assignment: {response.content}"
    )
    assert response.json()[0]["id"] == assignment_id, (
        f"Failed to get the correct assignment id: {response.content}"
    )
    assert response.json()[0]["due_date"] is not None, (
        f"Failed to get the correct due date: {response.content}"
    )

    response = client.get(
        "/api/v1/user/assignments",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 200, f"Failed to get assignment: {response.content}"
    assert len(response.json()) == 1, (
        f"Failed to get the correct assignment: {response.content}"
    )
    assert response.json()[0]["id"] == assignment_id, (
        f"Failed to get the correct assignment id: {response.content}"
    )
    assert response.json()[0]["due_date"] is None, (
        f"Incorrect behavior: {response.content}"
    )

    # Boundary cases
    response = client.get(
        "/api/v1/user/assignments",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, f"Failed to get assignment: {response.content}"
    assert len(response.json()) == 0, (
        f"Failed to get the correct assignment: {response.content}"
    )
    # No assignment assigned to admin, so the length should be 0

    # Unexpected cases
    response = client.post(
        "/api/v1/user/assignments",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 405, (
        f"Failed to get 405 method not allowed: {response.content}"
    )

    response = client.get(
        "/api/v1/user/assignments",
    )
    assert response.status_code == 401, (
        f"Failed to get 401 unauthorised: {response.content}"
    )


def test_get_assignment_review(
    client, student_token, teacher_token, assignment_id, class_id
):
    """Test the /api/v1/user/assignment/review endpoint

    Args:
        client (TestClient): The test client
        student_token (str): The student token
        teacher_token (str): The teacher token
        assignment_id (int): The assignment id
        class_id (int): The class id
    """
    # Expected cases
    response = client.get(
        "/api/v1/user/assignment/review",
        headers={"Authorization": f"Bearer {teacher_token}"},
        params={
            "assignment_id": assignment_id,
            "class_id": class_id,
        },
    )
    assert response.status_code == 200, (
        f"Failed to get assignment review: {response.content}"
    )

    # Boundary cases
    response = client.get(
        "/api/v1/user/assignment/review",
        headers={"Authorization": f"Bearer {student_token}"},
        params={
            "assignment_id": assignment_id,
            "class_id": class_id,
        },
    )
    assert response.status_code == 403, (
        f"Failed to get 403 forbidden: {response.content}"
    )

    response = client.get(
        "/api/v1/user/assignment/review",
        headers={"Authorization": f"Bearer {teacher_token}"},
        params={
            "assignment_id": 11111111,  # Invalid assignment id
            "class_id": class_id,
        },
    )
    assert response.status_code == 404, (
        f"Failed to get 404 not found: {response.content}"
    )

    response = client.get(
        "/api/v1/user/assignment/review",
        headers={"Authorization": f"Bearer {teacher_token}"},
        params={
            "assignment_id": assignment_id,
            "class_id": 11111111,  # Invalid class id
        },
    )
    assert response.status_code == 404, (
        f"Failed to get 404 not found: {response.content}"
    )

    # Unexpected cases
    response = client.post(
        "/api/v1/user/assignment/review",
        headers={"Authorization": f"Bearer {teacher_token}"},
        params={
            "assignment_id": assignment_id,
            "class_id": class_id,
        },
    )
    assert response.status_code == 405, (
        f"Failed to get 405 method not allowed: {response.content}"
    )

    response = client.get(
        "/api/v1/user/assignment/review",
        params={
            "assignment_id": assignment_id,
            "class_id": class_id,
        },
    )
    assert response.status_code == 401, (
        f"Failed to get 401 unauthorised: {response.content}"
    )


def test_submit(
    client,
    student_token,
    admin_token,
    sub_question_id,
    assignment_id,
    class_id,
    httpx_mock,
):
    """Test the /api/v1/user/submit endpoint

    Args:
        client (TestClient): The test client
        student_token (str): The student token
        admin_token (str): The admin token
        sub_question_id (int): The sub question id
        assignment_id (int): The assignment id
        class_id (int): The class id
        httpx_mock (HTTPXMock): The HTTPX mocker
    """
    httpx_mock.add_callback(llm_api_callback, method="POST", is_reusable=True)
    class_id = class_id  # Ensure the assignment is assigned to a class

    # Expected cases
    response = client.post(
        "/api/v1/user/submit",
        json={
            "assignment_id": assignment_id,
            "sub_question_id": sub_question_id,
            "answer": "This is a test answer",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, f"Failed to submit answer: {response.content}"

    # Boundary cases
    response = client.post(
        "/api/v1/user/submit",
        json={
            "assignment_id": 11111111,  # Invalid assignment id
            "sub_question_id": sub_question_id,
            "answer": "This is a test answer",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 404, (
        f"Failed to get 404 not found: {response.content}"
    )

    response = client.post(
        "/api/v1/user/submit",
        json={
            "assignment_id": assignment_id,
            "sub_question_id": 11111111,  # Invalid sub question id
            "answer": "This is a test answer",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 404, (
        f"Failed to get 404 not found: {response.content}"
    )

    response = client.post(
        "/api/v1/user/submit",
        json={
            "assignment_id": assignment_id,
            "sub_question_id": sub_question_id,
            "answer": "This is a test answer",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 403, (
        f"Failed to get 403 forbidden: {response.content}"
    )  # Admin is not in the class, so cannot submit

    # Unexpected cases
    response = client.get(
        "/api/v1/user/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        params={
            "assignment_id": assignment_id,
            "sub_question_id": sub_question_id,
            "answer": "This is a test answer",
        },
    )
    assert response.status_code == 405, (
        f"Failed to get 405 method not allowed: {response.content}"
    )

    response = client.post(
        "/api/v1/user/submit",
        json={
            "assignment_id": assignment_id,
            "sub_question_id": sub_question_id,
            # missing answer field
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 422, (
        f"Failed to get 422 unprocessable entity: {response.content}"
    )


def test_get_questions(client, student_token, admin_token, teacher_token):
    """Test the /api/v1/user/questions endpoint

    Args:
        client (TestClient): The test client
        student_token (str): The student token
        admin_token (str): The admin token
        teacher_token (str): The teacher token
    """
    # Expected cases
    response = client.get(
        "/api/v1/user/questions",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, f"Failed to get questions: {response.content}"
    assert len(response.json()) > 0, (
        f"Failed to get the correct number of questions: {response.content}"
    )

    response = client.get(
        "/api/v1/user/questions",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 200, f"Failed to get questions: {response.content}"
    assert len(response.json()) == 0, (
        f"Failed to get the correct number of questions: {response.content}"
    )

    # Boundary cases
    response = client.get(
        "/api/v1/user/questions",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, f"Failed to get questions: {response.content}"
    assert len(response.json()) == 0, (
        f"Failed to get the correct number of questions: {response.content}"
    )

    # Unexpected cases
    response = client.post(
        "/api/v1/user/questions",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 405, (
        f"Failed to get 405 method not allowed: {response.content}"
    )

    response = client.get(
        "/api/v1/user/questions",
    )
    assert response.status_code == 401, (
        f"Failed to get 401 unauthorized: {response.content}"
    )


def test_reset_password(client):
    """Test the /api/v1/user/password/reset endpoint

    Args:
        client (TestClient): The test client
    """
    # Register a new user for testing
    response = client.post(
        "/api/v1/user/register",
        json={
            "username": "reset_user",
            "email": "123@123abc.com",
            "display_name": "Reset User",
            "password": "first_password",
            "permission": Permission.STUDENT.value,
        },
    )
    assert response.status_code == 200, (
        f"Failed to register reset user: {response.content}"
    )
    response = client.post(
        "/api/v1/user/token",
        headers={
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "username": "reset_user",
            "password": "first_password",
        },
    )
    assert response.status_code == 200, (
        f"Failed to get reset user token: {response.content}"
    )
    token = response.json()["access_token"]

    # Expected cases
    response = client.post(
        "/api/v1/user/password/reset",
        json={
            "old_password": "first_password",
            "new_password": "new_password",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Failed to reset password: {response.content}"
    # Now the password is changed, so we need to get a new token
    response = client.post(
        "/api/v1/user/token",
        data={
            "username": "reset_user",
            "password": "new_password",
        },
    )
    assert response.status_code == 200, (
        f"Failed to get token with new password: {response.content}"
    )
    new_token = response.json()["access_token"]

    # Boundary cases
    response = client.post(
        "/api/v1/user/password/reset",
        json={
            "old_password": "wrong_password",  # Incorrect old password
            "new_password": "new_password",
        },
        headers={"Authorization": f"Bearer {new_token}"},
    )
    assert response.status_code == 400, (
        f"Failed to get 400 bad request: {response.content}"
    )

    response = client.post(
        "/api/v1/user/password/reset",
        json={
            "old_password": "new_password",
            "new_password": "new_password",  # New password is the same as old password
        },
        headers={"Authorization": f"Bearer {new_token}"},
    )
    assert response.status_code == 400, (
        f"Failed to get 400 bad request: {response.content}"
    )


def test_kick_student(client):
    """Test the /api/v1/user/class/kick endpoint"""
    response = client.post(
        "/api/v1/user/register",
        json={
            "username": "leave_student",
            "email": "12121@idkwhasd.com",
            "display_name": "Leave Student",
            "password": "leave_student_password",
            "permission": Permission.STUDENT.value,
        },
    )
    assert response.status_code == 200, (
        f"Failed to register leave student: {response.content}"
    )
    student_id = response.json()["id"]
    response = client.post(
        "/api/v1/user/token",
        headers={
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "username": "leave_student",
            "password": "leave_student_password",
        },
    )
    assert response.status_code == 200, (
        f"Failed to get leave student token: {response.content}"
    )
    student_token = response.json()["access_token"]

    response = client.post(
        "/api/v1/user/register",
        json={
            "username": "leave_teacher",
            "email": "121121@idkwhasd.com",
            "display_name": "Leave Teacher",
            "password": "leave_teacher_password",
            "permission": Permission.TEACHER.value,
        },
    )
    assert response.status_code == 200, (
        f"Failed to register leave teacher: {response.content}"
    )
    teacher_id = response.json()["id"]
    response = client.post(
        "/api/v1/user/token",
        headers={
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "username": "leave_teacher",
            "password": "leave_teacher_password",
        },
    )
    assert response.status_code == 200, (
        f"Failed to get leave teacher token: {response.content}"
    )
    teacher_token = response.json()["access_token"]

    response = client.post(
        "/api/v1/user/class/create",
        json={
            "class_name": "Leave Class",
            "enter_code": "leave_code",
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to create class for leave teacher: {response.content}"
    )
    class_name = response.json()["name"]

    response = client.post(
        "/api/v1/user/class/join",
        json={"enter_code": "leave_code", "class_name": class_name},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to join class as leave student: {response.content}"
    )

    response = client.post(
        "/api/v1/user/class/kick",
        json={"student_id": student_id},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 200, f"Failed to kick student: {response.content}"

    # Boundary cases
    response = client.post(
        "/api/v1/user/class/kick",
        json={"student_id": teacher_id},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 403, (
        f"Failed to get 403 forbidden: {response.content}"
    )  # the teacher is not enrolled in a class, so cannot kick

    response = client.post(
        "/api/v1/user/class/kick",
        json={"student_id": student_id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, (
        f"Failed to get 403 forbidden: {response.content}"
    )  # the student is already kicked, so cannot kick again

    # Unexpected cases
    response = client.get(
        "/api/v1/user/class/kick",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 405, (
        f"Failed to get 405 method not allowed: {response.content}"
    )
    response = client.post("/api/v1/user/class/kick")
    assert response.status_code == 401, (
        f"Failed to get 401 unauthorised: {response.content}"
    )
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_get_completed_sub_questions(
    client,
    student_token,
    admin_token,
    teacher_token,
    sub_question_id,
    assignment_id,
    class_id,
    httpx_mock,
):
    """Test the /api/v1/user/sub-questions/completed endpoint

    Args:
        client (TestClient): The test client
        student_token (str): The student token
        admin_token (str): The admin token
        teacher_token (str): The teacher token
        sub_question_id (int): The sub question id
        assignment_id (int): The assignment id
        class_id (int): The class id
        httpx_mock (HTTPXMock): The HTTPX mocker
    """
    httpx_mock.add_callback(llm_api_callback, method="POST", is_reusable=True)

    class_id = class_id
    response = client.post(
        "/api/v1/user/submit",
        json={
            "assignment_id": assignment_id,
            "sub_question_id": sub_question_id,
            "answer": "This is a test answer for completed sub-questions",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, f"Failed to submit answer: {response.content}"

    # Expected cases
    response = client.get(
        "/api/v1/user/sub-questions/completed",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to get completed sub-questions: {response.content}"
    )
    assert len(response.json()) >= 1, (
        f"Should have at least 1 completed sub-question: {response.content}"
    )
    assert response.json()[0]["id"] == sub_question_id, (
        f"Sub-question ID should match: {response.content}"
    )
    assert "submitted_answer" in response.json()[0], (
        f"Should include submitted_answer: {response.content}"
    )
    assert "performance" in response.json()[0], (
        f"Should include performance: {response.content}"
    )
    assert "feedback" in response.json()[0], (
        f"Should include feedback: {response.content}"
    )

    response = client.get(
        "/api/v1/user/sub-questions/completed",
        params={"assignment_id": assignment_id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to get completed sub-questions with assignment filter: {response.content}"
    )
    assert len(response.json()) >= 1, (
        f"Should have at least 1 completed sub-question for assignment: {response.content}"
    )

    response = client.get(
        "/api/v1/user/sub-questions/completed",
        params={"assignment_id": 99999999},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to get completed sub-questions with invalid assignment filter: {response.content}"
    )
    assert len(response.json()) == 0, (
        f"Should have no completed sub-questions for invalid assignment: {response.content}"
    )

    # Boundary cases
    response = client.get(
        "/api/v1/user/sub-questions/completed",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to get completed sub-questions for admin: {response.content}"
    )
    assert len(response.json()) == 0, (
        f"Admin should have no completed sub-questions: {response.content}"
    )

    response = client.get(
        "/api/v1/user/sub-questions/completed",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to get completed sub-questions for teacher: {response.content}"
    )
    assert len(response.json()) == 0, (
        f"Teacher should have no completed sub-questions: {response.content}"
    )

    # Unexpected cases
    response = client.post(
        "/api/v1/user/sub-questions/completed",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 405, (
        f"Failed to get 405 method not allowed: {response.content}"
    )

    response = client.get(
        "/api/v1/user/sub-questions/completed",
    )
    assert response.status_code == 401, (
        f"Failed to get 401 unauthorised: {response.content}"
    )


def test_get_completed_questions(
    client,
    student_token,
    admin_token,
    teacher_token,
):
    """Test the /api/v1/user/questions/completed endpoint

    Args:
        client (TestClient): The test client
        student_token (str): The student token
        admin_token (str): The admin token
        teacher_token (str): The teacher token
        question_id (int): The question id
    """
    # Expected cases
    response = client.get(
        "/api/v1/user/questions/completed",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to get completed questions: {response.content}"
    )
    assert len(response.json()) >= 1, (
        f"Should have at least 1 completed question: {response.content}"
    )

    # Boundary cases
    response = client.get(
        "/api/v1/user/questions/completed",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to get completed questions for admin: {response.content}"
    )
    assert len(response.json()) == 0, (
        f"Admin should have no completed questions: {response.content}"
    )

    response = client.get(
        "/api/v1/user/questions/completed",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to get completed questions for teacher: {response.content}"
    )
    assert len(response.json()) == 0, (
        f"Teacher should have no completed questions: {response.content}"
    )

    # Unexpected cases
    response = client.post(
        "/api/v1/user/questions/completed",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 405, (
        f"Failed to get 405 method not allowed: {response.content}"
    )

    response = client.get(
        "/api/v1/user/questions/completed",
    )
    assert response.status_code == 401, (
        f"Failed to get 401 unauthorised: {response.content}"
    )


def test_get_completed_question(
    client,
    student_token,
    assignment_id,
    admin_token,
    teacher_token,
    question_id,
    sub_question_id,
    httpx_mock,
):
    """Test the /api/v1/user/question/completed endpoint

    Args:
        client (TestClient): The test client
        student_token (str): The student token
        assignment_id (int): The assignment id
        admin_token (str): The admin token
        teacher_token (str): The teacher token
        question_id (int): The question id
        sub_question_id (int): The sub question id
        httpx_mock (HTTPXMock): The HTTPX mocker
    """
    httpx_mock.add_callback(llm_api_callback, method="POST", is_reusable=True)

    response = client.post(
        "/api/v1/user/submit",
        json={
            "assignment_id": assignment_id,
            "sub_question_id": sub_question_id,
            "answer": "This is another test answer for completed sub-questions",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, f"Failed to submit answer: {response.content}"

    # Expected cases
    response = client.get(
        "/api/v1/user/question/completed",
        params={"question_id": question_id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to get completed question: {response.content}"
    )
    completed_question = response.json()
    assert completed_question["id"] == question_id, (
        f"Question ID should match: {response.content}"
    )
    assert "sub_questions" in completed_question, (
        f"Should include sub_questions: {response.content}"
    )
    assert len(completed_question["sub_questions"]) >= 1, (
        f"Should have at least 1 completed sub-question: {response.content}"
    )

    sub_question = completed_question["sub_questions"][0]
    assert sub_question["id"] == sub_question_id, (
        f"Sub-question ID should match: {response.content}"
    )
    assert "submitted_answer" in sub_question, (
        f"Should include submitted_answer: {response.content}"
    )
    assert "performance" in sub_question, (
        f"Should include performance: {response.content}"
    )
    assert "feedback" in sub_question, f"Should include feedback: {response.content}"

    # Boundary cases
    response = client.get(
        "/api/v1/user/question/completed",
        params={"question_id": 99999999},  # Invalid question ID
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 404, (
        f"Should fail with invalid question ID: {response.content}"
    )

    response = client.get(
        "/api/v1/user/question/completed",
        params={"question_id": question_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, (
        f"Should fail when admin has no completed questions: {response.content}"
    )

    response = client.get(
        "/api/v1/user/question/completed",
        params={"question_id": question_id},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 404, (
        f"Should fail when teacher has no completed questions: {response.content}"
    )

    # Unexpected cases
    response = client.post(
        "/api/v1/user/question/completed",
        params={"question_id": question_id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 405, (
        f"Failed to get 405 method not allowed: {response.content}"
    )

    response = client.get(
        "/api/v1/user/question/completed",
        params={"question_id": question_id},
    )
    assert response.status_code == 401, (
        f"Failed to get 401 unauthorised: {response.content}"
    )

    response = client.get(
        "/api/v1/user/question/completed",
        # missing question_id
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 422, (
        f"Failed to get 422 unprocessable entity: {response.content}"
    )


def test_get_assignment_image(client, student_token, assignment_id, teacher_token):
    """Test the /api/v1/user/assignment/image/get endpoint

    Args:
        client (TestClient): The test client
        student_token (str): The student token
        assignment_id (int): The assignment id
        teacher_token (str): The teacher token
    """
    # Expected cases
    response = client.get(
        "/api/v1/user/assignment/image/get",
        params={"assignment_id": assignment_id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 204, (
        f"Failed to get assignment image: {response.content}"
    )

    response = client.get(
        "/api/v1/user/assignment/image/get",
        params={"assignment_id": assignment_id},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 204, (
        f"Failed to get assignment image: {response.content}"
    )

    # Boundary cases
    response = client.get(
        "/api/v1/user/assignment/image/get",
        params={"assignment_id": 99999999},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 404, (
        f"Should fail with invalid assignment ID: {response.content}"
    )

    # Unexpected cases
    response = client.post(
        "/api/v1/user/assignment/image/get",
        params={"assignment_id": assignment_id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 405, (
        f"Failed to get 405 method not allowed: {response.content}"
    )

    response = client.get(
        "/api/v1/user/assignment/image/get",
        params={"assignment_id": assignment_id},
    )
    assert response.status_code == 401, (
        f"Failed to get 401 unauthorised: {response.content}"
    )


def test_get_class_data(
    client,
    student_token,
    admin_token,
    teacher_token,
    assignment_id,
    class_id,
):
    """Test the /api/v1/user/class/data endpoint

    Args:
        client (TestClient): The test client
        student_token (str): The student token
        admin_token (str): The admin token
        teacher_token (str): The teacher token
        assignment_id (int): The assignment id
        class_id (int): The class id
    """
    class_id = class_id  # Ensure the student is in a class and assignment is assigned

    # Expected cases
    response = client.get(
        "/api/v1/user/class/data",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, f"Failed to get class data: {response.content}"
    class_data = response.json()
    assert "class_name" in class_data, f"Should include class_name: {response.content}"
    assert "teacher_name" in class_data, (
        f"Should include teacher_name: {response.content}"
    )
    assert "to_do_assignments" in class_data, (
        f"Should include to_do_assignments: {response.content}"
    )
    assert "done_assignments" in class_data, (
        f"Should include done_assignments: {response.content}"
    )
    all_assignments = class_data["to_do_assignments"] + class_data["done_assignments"]
    assignment_ids = [assignment["id"] for assignment in all_assignments]
    assert assignment_id in assignment_ids, (
        f"Assignment should be present in class data: {response.content}"
    )
    found_assignment = None
    for assignment in all_assignments:
        if assignment["id"] == assignment_id:
            found_assignment = assignment
            break
    assert found_assignment is not None, (
        f"Assignment should be found: {response.content}"
    )
    assert "due_date" in found_assignment, (
        f"Assignment should include due_date: {response.content}"
    )
    assert "question_ids" in found_assignment, (
        f"Assignment should include question_ids: {response.content}"
    )

    response = client.get(
        "/api/v1/user/class/data",
        headers={"Authorization": f"Bearer {teacher_token}"},
        params={"class_id": class_id},
    )
    assert response.status_code == 200, f"Failed to get class data: {response.content}"
    class_data = response.json()
    assert "name" in class_data, f"Should include name: {response.content}"
    assert "enter_code" in class_data, f"Should include enter_code: {response.content}"
    assert "students" in class_data, f"Should include students: {response.content}"
    assert "assignments" in class_data, (
        f"Should include assignments: {response.content}"
    )
    assert "performances" in class_data, (
        f"Should include performances: {response.content}"
    )

    # Boundary cases
    response = client.get(
        "/api/v1/user/class/data",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404, (
        f"Should fail when admin is not in a class: {response.content}"
    )

    response = client.get(
        "/api/v1/user/class/data",
        params={"class_id": 99999999},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 404, (
        f"Should fail with invalid class id: {response.content}"
    )

    # Unexpected cases
    response = client.post(
        "/api/v1/user/class/data",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 405, (
        f"Failed to get 405 method not allowed: {response.content}"
    )

    response = client.get(
        "/api/v1/user/class/data",
    )
    assert response.status_code == 401, (
        f"Failed to get 401 unauthorised: {response.content}"
    )
