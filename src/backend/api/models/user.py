from typing import Optional
from pydantic import BaseModel

from backend.types.user import Permission


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
    permission: Permission
