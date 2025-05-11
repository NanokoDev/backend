import jwt
from typing import Annotated
from datetime import datetime, timezone
from jwt.exceptions import InvalidTokenError
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status

from backend.config import config
from backend.db import user_manager
from backend.api.models.user import User, TokenData


def get_current_user_generator(oauth2_scheme: OAuth2PasswordBearer):
    """Generate a function to get the current user from the token.

    Args:
        oauth2_scheme (OAuth2PasswordBearer): OAuth2 scheme for token authentication.
    """

    async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
        """Get the current user from the token.

        Args:
            token (str): Token from the request.

        Raises:
            HTTPException: If the token is invalid or expired.

        Returns:
            User: The user object if the token is valid.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, config.jwt_secret, algorithms=["HS256"])
            username = payload.get("sub")
            if username is None:
                raise credentials_exception

            exp = payload.get("exp")
            if exp is None or datetime.fromtimestamp(
                exp, tz=timezone.utc
            ) < datetime.now(timezone.utc):
                raise credentials_exception

            token_data = TokenData(username=username)
        except InvalidTokenError:
            raise credentials_exception
        user = await user_manager.get_user_by_username(
            token_data.username
        ) or await user_manager.get_user_by_email(token_data.username)
        if user is None:
            raise credentials_exception
        return User(
            id=user.id,
            name=user.username,
            display_name=user.display_name,
            email=user.email,
            permission=user.permission,
        )

    return get_current_user
