import pytest

import backend.config as cfg
from backend.types.user import Permission

from .resources import llm_api_callback


question_id_cache = None
sub_question_id_cache = None
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
    global question_id_cache
    if question_id_cache is not None:
        return question_id_cache
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
    assert response.status_code == 400, (
        f"Failed to get 400 bad request: {response.content}"
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


def test_leave_class(client):
    """Test the /api/v1/user/class/leave endpoint

    Args:
        client (TestClient): The test client
    """
    # Register a new student and a teacher for testing
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

    # Create a class for the teacher
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

    # Join the class as a student
    response = client.post(
        "/api/v1/user/class/join",
        json={"enter_code": "leave_code", "class_name": class_name},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to join class as leave student: {response.content}"
    )

    # Leave the class as a student
    # Expected cases
    response = client.post(
        "/api/v1/user/class/leave",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, (
        f"Failed to leave class as leave student: {response.content}"
    )

    # Boundary cases
    response = client.post(
        "/api/v1/user/class/leave",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 403, (
        f"Failed to get 403 forbidden: {response.content}"
    )  # the teacher is not enrolled in a class, so cannot leave

    response = client.post(
        "/api/v1/user/class/leave",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403, (
        f"Failed to get 403 forbidden: {response.content}"
    )  # the student is already left the class, so cannot leave again

    # Unexpected cases
    response = client.get(
        "/api/v1/user/class/leave",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 405, (
        f"Failed to get 405 method not allowed: {response.content}"
    )
    response = client.post(
        "/api/v1/user/class/leave",
        # Missing Authorization header
    )
    assert response.status_code == 401, (
        f"Failed to get 401 unauthorised: {response.content}"
    )
    assert response.headers["WWW-Authenticate"] == "Bearer"
