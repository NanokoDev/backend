import jwt
from typing import Annotated
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from backend.config import config
from backend.db.user import UserManager
from backend.api.base import database_manager
from backend.api.models.user import Token, TokenData, User


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter(prefix="/user")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
user_manager = UserManager(database_manager=database_manager)


async def authenticate_user(username: str, password: str):
    """Authenticate a user with username (or email) and password.

    Args:
        username (str): Username or email of the user.
        password (str): Password of the user.

    Returns:
        Union[User, bool]: User object if authentication is successful, otherwise False.
    """
    user = await user_manager.get_user_by_email(
        username
    ) or await user_manager.get_user_by_username(username)
    if not user:
        return False
    if not user_manager.is_correct_password(user.id, password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create an access token with expiration time.

    Args:
        data (dict): Data to encode in the token.
        expires_delta (timedelta | None, optional): After how long the token will expire. Defaults to None.

    Returns:
        str: Encoded JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": int(expire.uctnow().timestamp())})
    encoded_jwt = jwt.encode(to_encode, config.jwt_secret, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """Get the current user from the token.

    Args:
        token (Annotated[str, Depends): Token from the request.

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
        payload = jwt.decode(token, config.jwt_secret, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception

        exp = payload.get("exp")
        if exp is None or datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(
            timezone.utc
        ):
            raise credentials_exception

        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = await user_manager.get_user_by_username(
        token_data.username
    ) or await user_manager.get_user_by_email(token_data.username)
    if user is None:
        raise credentials_exception
    return User(id=user.id, name=user.username, permission=user.permission)


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """Login for access token.

    Args:
        form_data (Annotated[OAuth2PasswordRequestForm, Depends): Form data containing username and password.

    Raises:
        HTTPException: If the username or password is incorrect.

    Returns:
        Token: The access token model.
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user
