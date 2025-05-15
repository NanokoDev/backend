import pytest
import datetime
import pytest_asyncio

from backend.db import user_manager, question_manager
from backend.types.user import Permission, Performance
from backend.types.question import ConceptType, ProcessType


@pytest_asyncio.fixture(loop_scope="session", scope="module")
def question_id(client, admin_token):
    """Add a question and return its ID

    Args:
        client (TestClient): the test client
        admin_token (str): the admin token

    Returns:
        int: the ID of the added question
    """
    question = {
        "source": "testing",
        "sub_questions": [
            {
                "description": "",
                "answer": "",
                "concept": ConceptType.ELEMENTS_OF_CHANCE.value,
                "process": ProcessType.FORMULATE.value,
            },
            {
                "description": "",
                "answer": "",
                "concept": ConceptType.ELEMENTS_OF_CHANCE.value,
                "process": ProcessType.APPLY.value,
            },
            {
                "description": "",
                "answer": "",
                "concept": ConceptType.ELEMENTS_OF_CHANCE.value,
                "process": ProcessType.EXPLAIN.value,
            },
            {
                "description": "",
                "answer": "",
                "concept": ConceptType.MATHEMATICAL_RELATIONSHIPS.value,
                "process": ProcessType.FORMULATE.value,
            },
            {
                "description": "",
                "answer": "",
                "concept": ConceptType.MATHEMATICAL_RELATIONSHIPS.value,
                "process": ProcessType.APPLY.value,
            },
            {
                "description": "",
                "answer": "",
                "concept": ConceptType.MATHEMATICAL_RELATIONSHIPS.value,
                "process": ProcessType.EXPLAIN.value,
            },
            {
                "description": "",
                "answer": "",
                "concept": ConceptType.OPERATIONS_ON_NUMBERS.value,
                "process": ProcessType.FORMULATE.value,
            },
            {
                "description": "",
                "answer": "",
                "concept": ConceptType.OPERATIONS_ON_NUMBERS.value,
                "process": ProcessType.APPLY.value,
            },
            {
                "description": "",
                "answer": "",
                "concept": ConceptType.OPERATIONS_ON_NUMBERS.value,
                "process": ProcessType.EXPLAIN.value,
            },
            {
                "description": "",
                "answer": "",
                "concept": ConceptType.OPERATIONS_ON_NUMBERS.value,
                "process": ProcessType.FORMULATE.value,
            },
            {
                "description": "",
                "answer": "",
                "concept": ConceptType.OPERATIONS_ON_NUMBERS.value,
                "process": ProcessType.APPLY.value,
            },
            {
                "description": "",
                "answer": "",
                "concept": ConceptType.OPERATIONS_ON_NUMBERS.value,
                "process": ProcessType.EXPLAIN.value,
            },
            {
                "description": "",
                "answer": "",
                "concept": ConceptType.MATHEMATICAL_RELATIONSHIPS.value,
                "process": ProcessType.FORMULATE.value,
            },
            {
                "description": "",
                "answer": "",
                "concept": ConceptType.ELEMENTS_OF_CHANCE.value,
                "process": ProcessType.EXPLAIN.value,
            },
            {
                "description": "",
                "answer": "",
                "concept": ConceptType.MATHEMATICAL_RELATIONSHIPS.value,
                "process": ProcessType.APPLY.value,
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


@pytest_asyncio.fixture(loop_scope="session", scope="module")
async def question(question_id):
    """Get the question by ID

    Args:
        question_id (int): the ID of the question

    Returns:
        Question: the question object
    """
    question = await question_manager.get_question(question_id=question_id)
    assert question is not None, "Question not found"
    return question


@pytest_asyncio.fixture(loop_scope="session", scope="module")
async def teacher():
    """Create a teacher user if it does not exist

    Returns:
        User: the teacher user object
    """
    teacher = await user_manager.get_user_by_username("service_teacher")

    if teacher is None:
        teacher = await user_manager.create_user(
            username="service_teacher",
            email="thisisnotanemail@abc.com",
            display_name="Service Teacher",
            password="123456",
            permission=Permission.TEACHER,
        )
    return teacher


@pytest_asyncio.fixture(loop_scope="session", scope="module")
async def class_(teacher, question):
    """Create a class if it does not exist

    Args:
        teacher (User): the teacher user object
        question (Question): the question object

    Returns:
        Class: the class object
    """
    class_ = await user_manager.get_class_by_name("Service Class")

    if class_ is None:
        class_ = await user_manager.create_class(
            teacher_id=teacher.id,
            class_name="Service Class",
            enter_code="service_class_code",
        )

    return class_


@pytest_asyncio.fixture(loop_scope="session", scope="module")
async def assignment(teacher, class_, question):
    """Create an assignment if it does not exist

    Args:
        teacher (User): the teacher user object
        class_ (Class): the class object
        question (Question): the question object

    Returns:
        Assignment: the assignment object
    """
    assignments = await user_manager.get_assignments_by_class_id(class_.id, teacher.id)

    if assignments:
        assignment = assignments[0]
    else:
        assignment = await user_manager.create_assignment(
            teacher_id=teacher.id,
            assignment_name="Service Assignment",
            assignment_description="Service Assignment Description",
            due_date=datetime.datetime.now() + datetime.timedelta(days=7),
            questions=[question],
        )
        await user_manager.assign_assignment_to_class(
            class_id=class_.id,
            assignment_id=assignment.id,
            teacher_id=teacher.id,
        )
    return assignment


@pytest_asyncio.fixture(loop_scope="session", scope="module")
async def student(class_, assignment, question):
    """Create a student user if it does not exist and enroll them in the class

    Args:
        class_ (Class): the class object
        assignment (Assignment): the assignment object
        question (Question): the question object

    Returns:
        User: the student user object
    """
    student = await user_manager.get_user_by_username("service_student")

    if student is None:
        student = await user_manager.create_user(
            username="service_student",
            email="thisisanemail@abc.com",
            display_name="Service Student",
            password="123456",
            permission=Permission.STUDENT,
        )

    if student.enrolled_class_id is None:
        await user_manager.join_class(
            user_id=student.id,
            class_id=class_.id,
            enter_code=class_.enter_code,
        )

        for i, sub_question in enumerate(question.sub_questions):
            await user_manager.add_completed_sub_question(
                user_id=student.id,
                sub_question_id=sub_question.id,
                assignment_id=assignment.id,
                answer=sub_question.answer,
                performance=Performance(i % Performance.__len__()),
                feedback="",
            )
    return student


@pytest_asyncio.fixture(loop_scope="session", scope="module")
async def service_teacher_token(client, teacher):
    """Get the service teacher token

    Args:
        client (TestClient): the test client
        teacher (User): the teacher user object

    Returns:
        str: the service teacher token
    """
    response = client.post(
        "/api/v1/user/token",
        headers={
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "username": "service_teacher",
            "password": "123456",
        },
    )
    assert response.status_code == 200, (
        f"Failed to get student token: {response.content}"
    )
    return response.json()["access_token"]


@pytest.mark.asyncio(loop_scope="session")(loop_scope="session")
async def test_get_performances(
    client, service_teacher_token, student, student_token, teacher_token
):
    """Test the /api/v1/service/performances endpoint

    Args:
        client (TestClient): the test client
        service_teacher_token (str): the service teacher token
        student (User): the student user object
        student_token (str): the student token
        teacher_token (str): the teacher token
    """
    # Expected cases
    resp = client.get(
        "/api/v1/service/performances",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={
            "user_id": student.id,
        },
    )
    assert resp.status_code == 200, resp.content
    assert resp.json() == {
        "operations_on_numbers": {
            "formulate": [1, 4],
            "apply": [2, 0],
            "explain": [3, 1],
        },
        "mathematical_relationships": {
            "formulate": [3, 2],
            "apply": [4, 4],
            "explain": [0],
        },
        "spatial_properties_and_representations": {
            "formulate": [],
            "apply": [],
            "explain": [],
        },
        "location_and_navigation": {
            "formulate": [],
            "apply": [],
            "explain": [],
        },
        "measurement": {
            "formulate": [],
            "apply": [],
            "explain": [],
        },
        "statistics_and_data": {
            "formulate": [],
            "apply": [],
            "explain": [],
        },
        "elements_of_chance": {
            "formulate": [0],
            "apply": [1],
            "explain": [2, 3],
        },
    }, f"Unexpected response: {resp.json()}"

    # Boundary cases
    resp = client.get(
        "/api/v1/service/performances",
        headers={"Authorization": f"Bearer {teacher_token}"},
        params={
            "user_id": student.id,
        },
    )
    assert resp.status_code == 403, resp.content

    resp = client.get(
        "/api/v1/service/performances",
        headers={"Authorization": f"Bearer {student_token}"},
        params={
            "user_id": student.id,
        },
    )
    assert resp.status_code == 403, resp.content

    resp = client.get(
        "/api/v1/service/performances",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={
            "user_id": 12345678,
        },
    )
    assert resp.status_code == 404, resp.content

    # Unexpected cases
    resp = client.get(
        "/api/v1/service/performances",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={},
    )
    assert resp.status_code == 422, resp.content

    resp = client.get(
        "/api/v1/service/performances",
        params={
            "user_id": student.id,
        },
    )
    assert resp.status_code == 401, resp.content


@pytest.mark.asyncio(loop_scope="session")
async def test_get_best_performances(
    client, service_teacher_token, student, student_token, teacher_token
):
    """Test the /api/v1/service/performances/best endpoint

    Args:
        client (TestClient): the test client
        service_teacher_token (str): the service teacher token
        student (User): the student user object
        student_token (str): the student token
        teacher_token (str): the teacher token
    """
    # Expected cases
    resp = client.get(
        "/api/v1/service/performances/best",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={
            "user_id": student.id,
        },
    )
    assert resp.status_code == 200, resp.content
    assert resp.json() == {
        "operations_on_numbers": {
            "formulate": 4.0,
            "apply": 2.0,
            "explain": 3.0,
        },
        "mathematical_relationships": {
            "formulate": 3.0,
            "apply": 4.0,
            "explain": 0.0,
        },
        "spatial_properties_and_representations": {
            "formulate": 0.0,
            "apply": 0.0,
            "explain": 0.0,
        },
        "location_and_navigation": {
            "formulate": 0.0,
            "apply": 0.0,
            "explain": 0.0,
        },
        "measurement": {
            "formulate": 0.0,
            "apply": 0.0,
            "explain": 0.0,
        },
        "statistics_and_data": {
            "formulate": 0.0,
            "apply": 0.0,
            "explain": 0.0,
        },
        "elements_of_chance": {
            "formulate": 0.0,
            "apply": 1.0,
            "explain": 3.0,
        },
    }, f"Unexpected response: {resp.json()}"

    # Boundary cases
    resp = client.get(
        "/api/v1/service/performances/best",
        headers={"Authorization": f"Bearer {teacher_token}"},
        params={
            "user_id": student.id,
        },
    )
    assert resp.status_code == 403, resp.content

    resp = client.get(
        "/api/v1/service/performances/best",
        headers={"Authorization": f"Bearer {student_token}"},
        params={
            "user_id": student.id,
        },
    )
    assert resp.status_code == 403, resp.content

    resp = client.get(
        "/api/v1/service/performances/best",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={
            "user_id": 12345678,
        },
    )
    assert resp.status_code == 404, resp.content

    # Unexpected cases
    resp = client.get(
        "/api/v1/service/performances/best",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={},
    )
    assert resp.status_code == 422, resp.content

    resp = client.get(
        "/api/v1/service/performances/best",
        params={
            "user_id": student.id,
        },
    )
    assert resp.status_code == 401, resp.content


@pytest.mark.asyncio(loop_scope="session")
async def test_get_average_performances(
    client, service_teacher_token, student, student_token, teacher_token
):
    """Test the /api/v1/service/performances/average endpoint

    Args:
        client (TestClient): the test client
        service_teacher_token (str): the service teacher token
        student (User): the student user object
        student_token (str): the student token
        teacher_token (str): the teacher token
    """
    # Expected cases
    resp = client.get(
        "/api/v1/service/performances/average",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={
            "user_id": student.id,
        },
    )
    assert resp.status_code == 200, resp.content
    assert resp.json() == {
        "operations_on_numbers": {
            "formulate": 2.5,
            "apply": 1.0,
            "explain": 2.0,
        },
        "mathematical_relationships": {
            "formulate": 2.5,
            "apply": 4.0,
            "explain": 0.0,
        },
        "spatial_properties_and_representations": {
            "formulate": 0.0,
            "apply": 0.0,
            "explain": 0.0,
        },
        "location_and_navigation": {
            "formulate": 0.0,
            "apply": 0.0,
            "explain": 0.0,
        },
        "measurement": {
            "formulate": 0.0,
            "apply": 0.0,
            "explain": 0.0,
        },
        "statistics_and_data": {
            "formulate": 0.0,
            "apply": 0.0,
            "explain": 0.0,
        },
        "elements_of_chance": {
            "formulate": 0.0,
            "apply": 1.0,
            "explain": 2.5,
        },
    }, f"Unexpected response: {resp.json()}"

    # Boundary cases
    resp = client.get(
        "/api/v1/service/performances/average",
        headers={"Authorization": f"Bearer {teacher_token}"},
        params={
            "user_id": student.id,
        },
    )
    assert resp.status_code == 403, resp.content

    resp = client.get(
        "/api/v1/service/performances/average",
        headers={"Authorization": f"Bearer {student_token}"},
        params={
            "user_id": student.id,
        },
    )
    assert resp.status_code == 403, resp.content

    resp = client.get(
        "/api/v1/service/performances/average",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={
            "user_id": 12345678,
        },
    )
    assert resp.status_code == 404, resp.content

    # Unexpected cases
    resp = client.get(
        "/api/v1/service/performances/average",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={},
    )
    assert resp.status_code == 422, resp.content

    resp = client.get(
        "/api/v1/service/performances/average",
        params={
            "user_id": student.id,
        },
    )
    assert resp.status_code == 401, resp.content


@pytest.mark.asyncio(loop_scope="session")
async def test_get_recent_best_performances(
    client, service_teacher_token, student, student_token, teacher_token
):
    """Test the /api/v1/service/performances/best/recent endpoint

    Args:
        client (TestClient): the test client
        service_teacher_token (str): the service teacher token
        student (User): the student user object
        student_token (str): the student token
        teacher_token (str): the teacher token
    """
    # Expected cases
    resp = client.get(
        "/api/v1/service/performances/best/recent",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={
            "user_id": student.id,
            "start_time": (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 200, resp.content
    assert resp.json() == {
        "operations_on_numbers": {
            "formulate": 4,
            "apply": 2,
            "explain": 3,
        },
        "mathematical_relationships": {
            "formulate": 3,
            "apply": 4,
            "explain": 0,
        },
        "spatial_properties_and_representations": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "location_and_navigation": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "measurement": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "statistics_and_data": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "elements_of_chance": {
            "formulate": 0,
            "apply": 1,
            "explain": 3,
        },
    }, f"Unexpected response: {resp.json()}"

    resp = client.get(
        "/api/v1/service/performances/best/recent",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={
            "user_id": student.id,
            "start_time": (
                datetime.datetime.now() + datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 200, resp.content
    assert resp.json() == {
        "operations_on_numbers": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "mathematical_relationships": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "spatial_properties_and_representations": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "location_and_navigation": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "measurement": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "statistics_and_data": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "elements_of_chance": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
    }, f"Unexpected response: {resp.json()}"

    # Boundary cases
    resp = client.get(
        "/api/v1/service/performances/best/recent",
        headers={"Authorization": f"Bearer {teacher_token}"},
        params={
            "user_id": student.id,
            "start_time": (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 403, resp.content

    resp = client.get(
        "/api/v1/service/performances/best/recent",
        headers={"Authorization": f"Bearer {student_token}"},
        params={
            "user_id": student.id,
            "start_time": (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 403, resp.content

    resp = client.get(
        "/api/v1/service/performances/best/recent",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={
            "user_id": 12345678,
            "start_time": (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 404, resp.content

    # Unexpected cases
    resp = client.get(
        "/api/v1/service/performances/best/recent",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={},
    )
    assert resp.status_code == 422, resp.content

    resp = client.get(
        "/api/v1/service/performances/best/recent",
        params={
            "user_id": student.id,
            "start_time": (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 401, resp.content


@pytest.mark.asyncio(loop_scope="session")
async def test_get_recent_average_performances(
    client, service_teacher_token, student, student_token, teacher_token
):
    """Test the /api/v1/service/performances/average/recent endpoint

    Args:
        client (TestClient): the test client
        service_teacher_token (str): the service teacher token
        student (User): the student user object
        student_token (str): the student token
        teacher_token (str): the teacher token
    """
    # Expected cases
    resp = client.get(
        "/api/v1/service/performances/average/recent",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={
            "user_id": student.id,
            "start_time": (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 200, resp.content
    assert resp.json() == {
        "operations_on_numbers": {
            "formulate": 2.5,
            "apply": 1,
            "explain": 2,
        },
        "mathematical_relationships": {
            "formulate": 2.5,
            "apply": 4,
            "explain": 0,
        },
        "spatial_properties_and_representations": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "location_and_navigation": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "measurement": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "statistics_and_data": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "elements_of_chance": {
            "formulate": 0,
            "apply": 1,
            "explain": 2.5,
        },
    }, f"Unexpected response: {resp.json()}"

    resp = client.get(
        "/api/v1/service/performances/average/recent",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={
            "user_id": student.id,
            "start_time": (
                datetime.datetime.now() + datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 200, resp.content
    assert resp.json() == {
        "operations_on_numbers": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "mathematical_relationships": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "spatial_properties_and_representations": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "location_and_navigation": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "measurement": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "statistics_and_data": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "elements_of_chance": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
    }, f"Unexpected response: {resp.json()}"

    # Boundary cases
    resp = client.get(
        "/api/v1/service/performances/average/recent",
        headers={"Authorization": f"Bearer {teacher_token}"},
        params={
            "user_id": student.id,
            "start_time": (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 403, resp.content

    resp = client.get(
        "/api/v1/service/performances/average/recent",
        headers={"Authorization": f"Bearer {student_token}"},
        params={
            "user_id": student.id,
            "start_time": (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 403, resp.content

    resp = client.get(
        "/api/v1/service/performances/average/recent",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={
            "user_id": 12345678,
            "start_time": (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 404, resp.content

    # Unexpected cases
    resp = client.get(
        "/api/v1/service/performances/average/recent",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={},
    )
    assert resp.status_code == 422, resp.content

    resp = client.get(
        "/api/v1/service/performances/average/recent",
        params={
            "user_id": student.id,
            "start_time": (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 401, resp.content


@pytest.mark.asyncio(loop_scope="session")
async def test_get_performance_trends(
    client, service_teacher_token, student, student_token, teacher_token
):
    """Test the /api/v1/service/performances/trends endpoint

    Args:
        client (TestClient): the test client
        service_teacher_token (str): the service teacher token
        student (User): the student user object
        student_token (str): the student token
        teacher_token (str): the teacher token
    """
    expected_trends = {
        "operations_on_numbers": {
            "formulate": 2,
            "apply": -2,
            "explain": -2,
        },
        "mathematical_relationships": {
            "formulate": -1,
            "apply": 0,
            "explain": 0,
        },
        "spatial_properties_and_representations": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "location_and_navigation": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "measurement": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "statistics_and_data": {
            "formulate": 0,
            "apply": 0,
            "explain": 0,
        },
        "elements_of_chance": {
            "formulate": 0,
            "apply": 0,
            "explain": 1,
        },
    }

    # Expected cases
    resp = client.get(
        "/api/v1/service/performances/trends",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={
            "user_id": student.id,
            "start_time": (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_trends, f"Unexpected response: {resp.json()}"

    resp = client.get(
        "/api/v1/service/performances/trends",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={
            "user_id": student.id,
        },
    )
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_trends, f"Unexpected response: {resp.json()}"

    # Boundary cases
    resp = client.get(
        "/api/v1/service/performances/trends",
        headers={"Authorization": f"Bearer {teacher_token}"},
        params={
            "user_id": student.id,
            "start_time": (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 403, resp.content

    resp = client.get(
        "/api/v1/service/performances/trends",
        headers={"Authorization": f"Bearer {student_token}"},
        params={
            "user_id": student.id,
            "start_time": (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 403, resp.content

    resp = client.get(
        "/api/v1/service/performances/trends",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={
            "user_id": 12345678,
            "start_time": (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 404, resp.content

    # Unexpected cases
    resp = client.get(
        "/api/v1/service/performances/trends",
        headers={"Authorization": f"Bearer {service_teacher_token}"},
        params={},
    )
    assert resp.status_code == 422, resp.content

    resp = client.get(
        "/api/v1/service/performances/trends",
        params={
            "user_id": student.id,
            "start_time": (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).isoformat()
            + "Z",
        },
    )
    assert resp.status_code == 401, resp.content
