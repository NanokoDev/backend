import jwt
from typing import Annotated
from fastapi.responses import JSONResponse
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from backend.config import config
from backend.db.user import UserManager
from backend.types.user import Permission
from backend.db.bank import QuestionManager
from backend.api.base import database_manager
from backend.api.models.user import Token, TokenData, User, FeedBack
from backend.exceptions.user import (
    UserIdInvalid,
    UserEmailInvalid,
    UsernameAlreadyExists,
    UserEmailAlreadyExists,
)


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter(prefix="/user")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
user_manager = UserManager(database_manager=database_manager)
question_manager = QuestionManager(database_manager=database_manager)


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
    try:
        user = await authenticate_user(form_data.username, form_data.password)
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
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


@router.get("/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


@router.get("/register", response_model=User)
async def register_user(
    username: str,
    email: str,
    display_name: str,
    password: str,
    permission: Permission,
):
    """Register a new user.

    Args:
        username (str): Username of the user.
        email (str): Email of the user.
        display_name (str): Display name of the user.
        password (str): Password of the user.
        permission (Permission): Permission level of the user.

    Returns:
        User: The created user object.
    """
    try:
        return await user_manager.create_user(
            username=username,
            email=email,
            display_name=display_name,
            password=password,
            permission=permission,
        )
    except UserEmailInvalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format",
        )
    except UserEmailAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )
    except UsernameAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/submit", response_model=FeedBack)
async def submit_answer(
    sub_question_id: int,
    answer: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Submit an answer for a sub-question.

    Args:
        sub_question_id (int): ID of the sub-question.
        answer (str): The answer to the sub-question.
        current_user (Annotated[User, Depends): Current user from the token.

    Raises:
        HTTPException: If the sub-question is not found.

    Returns:
        FeedBack: The feedback model containing the feedback text and performance from the LLM.
    """
    sub_question = await question_manager.get_sub_question(
        sub_question_id=sub_question_id
    )
    if not sub_question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sub-question not found",
        )

    # feedback, performance = llm_manager.get_feedback(
    #     question=sub_question.question, answer=answer
    # )
    # TODO: Implement the LLM manager to get feedback and performance.

    from backend.types.user import Performance

    feedback = "This is a feedback"
    performance = Performance.FAMILIAR

    await user_manager.add_completed_sub_question(
        user=await user_manager.get_user_by_id(current_user.id),
        sub_question=sub_question,
        performance=performance,
        feedback=feedback,
    )

    return FeedBack(
        text=feedback,
        performance=performance,
    )


@router.get("/reset_password")
async def reset_password(
    old_password: str,
    new_password: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Reset the password for the current user.

    Args:
        old_password (str): The old password of the user.
        new_password (str): The new password to set for the user.
        current_user (Annotated[User, Depends): Current user from the token.

    Raises:
        HTTPException: If the old password is incorrect or the new password is the same as the old password.

    Returns:
        JSONResponse: A JSON response indicating the success of the password reset.
    """
    if not await user_manager.is_correct_password(current_user.id, old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )
    if old_password == new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as old password",
        )
    await user_manager.reset_password(
        user_id=current_user.id,
        new_password=new_password,
    )
    return JSONResponse(
        content={"message": "Password reset successfully"},
        status_code=status.HTTP_200_OK,
    )
