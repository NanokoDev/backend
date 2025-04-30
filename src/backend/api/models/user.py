from typing import Optional
from pydantic import BaseModel

from backend.types.user import Permission, Performance


class Token(BaseModel):
    """Token model for authentication"""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model"""

    username: Optional[str] = None


class User(BaseModel):
    """User model for API"""

    id: int
    name: str
    display_name: str
    email: str
    permission: Permission


class Class(BaseModel):
    """Class model for API"""

    id: int
    name: str
    enter_code: str
    teacher_id: int


class FeedBack(BaseModel):
    """Feedback model for API"""

    text: str
    performance: Performance


class Assignment(BaseModel):
    """Assignment model for API"""

    id: int
    name: str
    description: str
    teacher_id: int
