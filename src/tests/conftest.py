import shutil
import pytest
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient

from main import get_app
import backend.config as cfg
from backend.utils import load_config
from backend.types.user import Permission


admin_token_cache = None
student_token_cache = None
teacher_token_cache = None


def pytest_configure(config):
    """Runs before tests"""
    cfg.config = load_config(Path("src/tests/test_config.json"))
    cfg.config.image_store_path.mkdir(exist_ok=True, parents=True)

    from backend.api.user import user_manager
    from backend.api.base import database_manager
    # Import after configuration to avoid managers using the default config

    loop = asyncio.get_event_loop()
    loop.run_until_complete(database_manager.init())
    loop.run_until_complete(
        user_manager._create_user(
            username=cfg.config.admin_username,
            email=cfg.config.admin_email,
            display_name=cfg.config.admin_display_name,
            password=cfg.config.admin_password,
            permission=Permission.ADMIN,
        )
    )


def pytest_unconfigure(config):
    """Runs after tests"""
    if cfg.config.image_store_path.exists():
        shutil.rmtree("temp_data")

    from backend.api.base import database_manager

    loop = asyncio.get_event_loop()
    loop.run_until_complete(database_manager.close())

    if cfg.config.bank_db_path is not None and cfg.config.bank_db_path.exists():
        cfg.config.bank_db_path.unlink()


@pytest.fixture(scope="session")
def client():
    """Get a test HTTP client

    Returns:
        TestClient: A test client that has same methods of httpx.Client
    """
    app = get_app()
    return TestClient(app)


@pytest.fixture(scope="session")
def admin_token(client):
    """Get the admin token

    Args:
        client (TestClient): The test client

    Returns:
        str: The admin token
    """
    global admin_token_cache
    if admin_token_cache is not None:
        return admin_token_cache
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "username": cfg.config.admin_username,
        "password": cfg.config.admin_password,
    }
    response = client.post("/api/v1/user/token", headers=headers, data=data)
    assert response.status_code == 200, f"Failed to get admin token: {response.content}"
    admin_token_cache = response.json()["access_token"]
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def student_token(client, admin_token):
    """Get the student token

    Args:
        client (TestClient): The test client
        admin_token (str): The admin token

    Returns:
        str: The student token
    """
    global student_token_cache
    if student_token_cache is not None:
        return student_token_cache

    # Register a new student user
    response = client.post(
        "/api/v1/user/register",
        json={
            "username": "student",
            "email": "student_email@example.com",
            "display_name": "Student",
            "password": "student_password",
            "permission": Permission.STUDENT.value,
        },
    )
    assert response.status_code == 200, (
        f"Failed to register student: {response.content}"
    )
    response = client.post(
        "/api/v1/user/token",
        headers={
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "username": "student",
            "password": "student_password",
        },
    )
    assert response.status_code == 200, (
        f"Failed to get student token: {response.content}"
    )
    student_token_cache = response.json()["access_token"]
    return student_token_cache


@pytest.fixture(scope="session")
def teacher_token(client, admin_token):
    """Get the teacher token

    Args:
        client (TestClient): The test client
        admin_token (str): The admin token

    Returns:
        str: The teacher token
    """
    global teacher_token_cache
    if teacher_token_cache is not None:
        return teacher_token_cache

    # Register a new teacher user
    response = client.post(
        "/api/v1/user/register",
        json={
            "username": "teacher",
            "email": "teacher_email@example.com",
            "display_name": "Teacher",
            "password": "teacher_password",
            "permission": Permission.TEACHER.value,
        },
    )
    assert response.status_code == 200, (
        f"Failed to register teacher: {response.content}"
    )
    response = client.post(
        "/api/v1/user/token",
        headers={
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "username": "teacher",
            "password": "teacher_password",
        },
    )
    assert response.status_code == 200, (
        f"Failed to get teacher token: {response.content}"
    )
    teacher_token_cache = response.json()["access_token"]
    return teacher_token_cache
