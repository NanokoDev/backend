import jwt
from typing import Annotated, List
from fastapi.responses import JSONResponse
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, APIRouter, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from backend.config import config
from backend.db.user import UserManager
from backend.types.user import Permission
from backend.db.bank import QuestionManager
from backend.api.base import database_manager
from backend.exceptions.bank import SubQuestionIdInvalid
from backend.api.models.user import Token, TokenData, User, FeedBack, Class, Assignment
from backend.exceptions.user import (
    UserIdInvalid,
    ClassIdInvalid,
    UserEmailInvalid,
    ClassAlreadyExists,
    AssignmentIdInvalid,
    UsernameAlreadyExists,
    UserEmailAlreadyExists,
    ClassEnterCodeIncorrect,
)


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter(prefix="/user", tags=["user"])
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
    if not await user_manager.is_correct_password(user.id, password):
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
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.jwt_secret, algorithm=ALGORITHM)
    return encoded_jwt


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
    return User(
        id=user.id,
        name=user.username,
        display_name=user.display_name,
        email=user.email,
        permission=user.permission,
    )


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """Login for access token.

    Args:
        form_data (OAuth2PasswordRequestForm): Form data containing username and password.

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


@router.post("/register", response_model=User)
async def register_user(
    username: str = Body(...),
    email: str = Body(...),
    display_name: str = Body(...),
    password: str = Body(...),
    permission: Permission = Body(...),
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
        db_user = await user_manager.create_user(
            username=username,
            email=email,
            display_name=display_name,
            password=password,
            permission=permission,
        )
        return User(
            id=db_user.id,
            name=db_user.username,
            display_name=db_user.display_name,
            email=db_user.email,
            permission=db_user.permission,
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
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.post("/submit", response_model=FeedBack)
async def submit_answer(
    sub_question_id: int = Body(...),
    assignment_id: int = Body(...),
    answer: str = Body(...),
    current_user: User = Depends(get_current_user),
):
    """Submit an answer for a sub-question.

    Args:
        sub_question_id (int): ID of the sub-question.
        assignment_id (int): ID of the assignment.
        answer (str): The answer to the sub-question.
        current_user (User): Current user from the token.

    Raises:
        HTTPException: If the user ID is invalid, assignment ID is invalid, or permission error occurs.

    Returns:
        FeedBack: The feedback model containing the feedback text and performance from the LLM.
    """

    # feedback, performance = llm_manager.get_feedback(
    #     question=sub_question.question, answer=answer
    # )
    # TODO: Implement the LLM manager to get feedback and performance.

    from backend.types.user import Performance

    feedback = "This is a feedback"
    performance = Performance.FAMILIAR

    try:
        await user_manager.add_completed_sub_question(
            user_id=current_user.id,
            sub_question_id=sub_question_id,
            assignment_id=assignment_id,
            answer=answer,
            performance=performance,
            feedback=feedback,
        )
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    except AssignmentIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not in a class or does not have permission to do this assignment",
        )
    except SubQuestionIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sub-question not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )

    return FeedBack(
        text=feedback,
        performance=performance,
    )


@router.post("/reset_password")
async def reset_password(
    old_password: str = Body(...),
    new_password: str = Body(...),
    current_user: User = Depends(get_current_user),
):
    """Reset the password for the current user.

    Args:
        old_password (str): The old password of the user.
        new_password (str): The new password to set for the user.
        current_user (User): Current user from the token.

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


@router.post("/create_class", response_model=Class)
async def create_class(
    class_name: str = Body(...),
    enter_code: str = Body(...),
    current_user: User = Depends(get_current_user),
):
    """Create a new class.

    Args:
        class_name (str): Name of the class.
        enter_code (str): Enter code for the class.
        current_user (User): Current user from the token.

    Raises:
        HTTPException: If the class name already exists or the user does not have permission to create a class, or the user ID is invalid.

    Returns:
        Class: The created class object.
    """
    try:
        class_ = await user_manager.create_class(
            class_name=class_name,
            enter_code=enter_code,
            teacher_id=current_user.id,
        )
        return Class(
            id=class_.id,
            name=class_.name,
            enter_code=class_.enter_code,
            teacher_id=class_.teacher_id,
        )
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid user ID",
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )
    except ClassAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class name already exists",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.post("/join_class", response_model=Class)
async def join_class(
    class_name: str = Body(...),
    enter_code: str = Body(...),
    current_user: User = Depends(get_current_user),
):
    """Join a class.

    Args:
        class_name (str): Name of the class.
        enter_code (str): Enter code for the class.
        current_user (User): Current user from the token.

    Raises:
        HTTPException: If the class name does not exist or the enter code is incorrect.

    Returns:
        Class: The joined class object.
    """
    try:
        class_ = await user_manager.get_class_by_name(class_name=class_name)
        if not class_:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found",
            )

        joint_class = await user_manager.join_class(
            user_id=current_user.id,
            class_id=class_.id,
            enter_code=enter_code,
        )
        return Class(
            id=joint_class.id,
            name=joint_class.name,
            enter_code=joint_class.enter_code,
            teacher_id=joint_class.teacher_id,
        )
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid user ID",
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is already in a class or trying to join their own class",
        )
    except ClassIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )
    except ClassEnterCodeIncorrect:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect enter code",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.post("/leave_class")
async def leave_class(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Leave the current class.

    Args:
        current_user (User): Current user from the token.

    Raises:
        HTTPException: If the user is not in a class.

    Returns:
        JSONResponse: A JSON response indicating the success of leaving the class.
    """
    try:
        await user_manager.leave_class(
            user_id=current_user.id,
        )
        return JSONResponse(
            content={"message": "Left class successfully"},
            status_code=status.HTTP_200_OK,
        )
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not in a class",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.post("/create_assignment", response_model=Assignment)
async def create_assignment(
    assignment_name: str = Body(...),
    description: str = Body(...),
    due_date: datetime = Body(...),
    question_ids: List[int] = Body(...),
    current_user: User = Depends(get_current_user),
):
    try:
        questions = await question_manager.get_questions_by_ids(
            question_ids=question_ids
        )
        assignment = await user_manager.create_assignment(
            teacher_id=current_user.id,
            assignment_name=assignment_name,
            assignment_description=description,
            due_date=due_date,
            questions=questions,
        )
        return Assignment(
            id=assignment.id,
            name=assignment.name,
            description=assignment.description,
            teacher_id=assignment.teacher_id,
        )
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to create an assignment",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.post("/assign_assignment")
async def assign_assignment(
    assignment_id: int = Body(...),
    class_id: int = Body(...),
    current_user: User = Depends(get_current_user),
):
    try:
        await user_manager.assign_assignment_to_class(
            assignment_id=assignment_id,
            class_id=class_id,
            teacher_id=current_user.id,
        )
        return JSONResponse(
            content={"message": "Assignment assigned to class successfully"},
            status_code=status.HTTP_200_OK,
        )
    except AssignmentIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to assign this assignment",
        )
    except ClassIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/get_assignments", response_model=List[Assignment])
async def get_assignments(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get all assignments for the current user.
    If the user is a teacher, get all assignments they created.
    If the user is a student, get all assignments assigned to their class.

    Args:
        current_user (User): Current user from the token.

    """
    try:
        if current_user.permission == Permission.TEACHER:
            assignments = await user_manager.get_assignments_by_teacher_id(
                teacher_id=current_user.id
            )
        else:
            assignments = await user_manager.get_assignments_by_student_id(
                student_id=current_user.id
            )
        return [
            Assignment(
                id=assignment.id,
                name=assignment.name,
                description=assignment.description,
                teacher_id=assignment.teacher_id,
            )
            for assignment in assignments
        ]
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to view assignments",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )
