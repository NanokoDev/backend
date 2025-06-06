import jwt
from typing import Annotated, List
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from backend.config import config
from backend.types.user import Permission
from backend.api.base import get_current_user_generator
from backend.exceptions.bank import SubQuestionIdInvalid
from backend.db import user_manager, llm_manager, question_manager
from backend.exceptions.llm import LLMRequestError, InvalidLLMResponse
from backend.api.models.user import (
    User,
    Token,
    Class,
    FeedBack,
    Assignment,
    JoinClassRequest,
    CreateClassRequest,
    UserRegisterRequest,
    SubmitAnswerRequest,
    ResetPasswordRequest,
    CreateAssignmentRequest,
    AssignAssignmentRequest,
)
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


ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter(prefix="/user", tags=["user"])
get_current_user = get_current_user_generator(OAuth2PasswordBearer(tokenUrl="token"))


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
    encoded_jwt = jwt.encode(to_encode, config.jwt_secret, algorithm="HS256")
    return encoded_jwt


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
    request: UserRegisterRequest,
):
    """Register a new user.

    Args:
        request (UserRegisterRequest): The request containing user registration details

    Returns:
        User: The created user object.
    """
    try:
        db_user = await user_manager.create_user(
            username=request.username,
            email=request.email,
            display_name=request.display_name,
            password=request.password,
            permission=request.permission,
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
    request: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
):
    """Submit an answer for a sub-question.

    Args:
        request (SubmitAnswerRequest): The request containing sub_question_id, assignment_id and answer
        current_user (User): Current user from the token.

    Raises:
        HTTPException: If the user ID is invalid, assignment ID is invalid, permission error occurs, or LLM request error occurs.

    Returns:
        FeedBack: The feedback model containing the feedback text and performance from the LLM.
    """
    try:
        feedback = await llm_manager.get_sub_question_feedback(
            sub_question_id=request.sub_question_id,
            answer=request.answer,
        )
    except SubQuestionIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sub-question not found",
        )
    except LLMRequestError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM request error",
        )
    except InvalidLLMResponse:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid LLM response",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )

    try:
        await user_manager.add_completed_sub_question(
            user_id=current_user.id,
            sub_question_id=request.sub_question_id,
            assignment_id=request.assignment_id,
            answer=request.answer,
            performance=feedback.performance,
            feedback=feedback.comment,
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
        comment=feedback.comment,
        performance=feedback.performance,
    )


@router.post("/password/reset")
async def reset_password(
    request: ResetPasswordRequest,
    current_user: User = Depends(get_current_user),
):
    """Reset the password for the current user.

    Args:
        request (ResetPasswordRequest): The request containing old and new passwords
        current_user (User): Current user from the token.

    Raises:
        HTTPException: If the old password is incorrect or the new password is the same as the old password.

    Returns:
        JSONResponse: A JSON response indicating the success of the password reset.
    """
    if not await user_manager.is_correct_password(
        current_user.id, request.old_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )
    if request.old_password == request.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as old password",
        )
    await user_manager.reset_password(
        user_id=current_user.id,
        new_password=request.new_password,
    )
    return JSONResponse(
        content={"message": "Password reset successfully"},
        status_code=status.HTTP_200_OK,
    )


@router.post("/class/create", response_model=Class)
async def create_class(
    request: CreateClassRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a new class.

    Args:
        request (CreateClassRequest): The request containing class_name and enter_code
        current_user (User): Current user from the token.

    Raises:
        HTTPException: If the class name already exists or the user does not have permission to create a class, or the user ID is invalid.

    Returns:
        Class: The created class object.
    """
    try:
        class_ = await user_manager.create_class(
            class_name=request.class_name,
            enter_code=request.enter_code,
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


@router.post("/class/join", response_model=Class)
async def join_class(
    request: JoinClassRequest,
    current_user: User = Depends(get_current_user),
):
    """Join a class.

    Args:
        request (JoinClassRequest): The request containing class_name and enter_code
        current_user (User): Current user from the token.

    Raises:
        HTTPException: If the class name does not exist or the enter code is incorrect.

    Returns:
        Class: The joined class object.
    """
    try:
        class_ = await user_manager.get_class_by_name(class_name=request.class_name)
        if not class_:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found",
            )

        joint_class = await user_manager.join_class(
            user_id=current_user.id,
            class_id=class_.id,
            enter_code=request.enter_code,
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


@router.post("/class/leave")
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


@router.post("/assignment/create", response_model=Assignment)
async def create_assignment(
    request: CreateAssignmentRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a new assignment.

    Args:
        request (CreateAssignmentRequest): The request containing assignment details
        current_user (User): Current user from the token.

    Raises:
        HTTPException: If the user does not have permission to create an assignment.

    Returns:
        Assignment: The created assignment object.
    """
    try:
        questions = await question_manager.get_questions_by_ids(
            question_ids=request.question_ids
        )
        assignment = await user_manager.create_assignment(
            teacher_id=current_user.id,
            assignment_name=request.assignment_name,
            assignment_description=request.description,
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


@router.post("/assignment/assign")
async def assign_assignment(
    request: AssignAssignmentRequest,
    current_user: User = Depends(get_current_user),
):
    """Assign an assignment to a class.

    Args:
        request (AssignAssignmentRequest): The request containing assignment_id and class_id
        current_user (User): Current user from the token.

    Raises:
        HTTPException: If the user does not have permission to assign the assignment.

    Returns:
        JSONResponse: A JSON response indicating the success of the assignment.
    """
    try:
        await user_manager.assign_assignment_to_class(
            assignment_id=request.assignment_id,
            class_id=request.class_id,
            teacher_id=current_user.id,
            due_date=request.due_date,
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


@router.get("/assignments", response_model=List[Assignment])
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
            return [
                Assignment(
                    id=assignment.id,
                    name=assignment.name,
                    description=assignment.description,
                    teacher_id=assignment.teacher_id,
                )
                for assignment in assignments
            ]
        else:
            assignments = await user_manager.get_assignments_by_student_id(
                student_id=current_user.id
            )
            return [
                Assignment(
                    id=assignment.assignment.id,
                    name=assignment.assignment.name,
                    description=assignment.assignment.description,
                    teacher_id=assignment.assignment.teacher_id,
                    due_date=assignment.due_date,
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
