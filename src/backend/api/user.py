import jwt
from collections import defaultdict
from fastapi.responses import JSONResponse
from typing import Annotated, List, Optional, Dict
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from backend.config import config
from backend.types.user import Permission
from backend.api.base import get_current_user_generator
from backend.exceptions.bank import SubQuestionIdInvalid
from backend.api.models.bank import SubQuestion, Question
from backend.db import user_manager, llm_manager, question_manager
from backend.exceptions.llm import LLMRequestError, InvalidLLMResponse
from backend.db.models.bank import Question as DBQuestion, CompletedSubQuestion
from backend.api.models.user import (
    User,
    Token,
    Class,
    FeedBack,
    ClassData,
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


@router.get("/sub-questions/completed", response_model=List[SubQuestion])
async def get_completed_sub_questions(
    assignment_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    """Get all completed sub-questions for the current user.

    Args:
        assignment_id (Optional[int]): The ID of the assignment. Defaults to None.
        current_user (User): Current user from the token.

    Returns:
        List[SubQuestion]: A list of sub-questions that the user has completed.
    """
    if assignment_id is not None:
        completed_sub_questions = await user_manager.get_completed_sub_questions(
            user_id=current_user.id, assignment_id=assignment_id
        )
    else:
        completed_sub_questions = await user_manager.get_completed_sub_questions(
            user_id=current_user.id
        )
    return [
        SubQuestion(
            id=completed_sub_question.sub_question_id,
            description=completed_sub_question.sub_question.description,
            answer=completed_sub_question.sub_question.answer,
            concept=completed_sub_question.sub_question.concept,
            process=completed_sub_question.sub_question.process,
            keywords=completed_sub_question.sub_question.keywords,
            options=completed_sub_question.sub_question.options,
            image_id=completed_sub_question.sub_question.image_id,
            submitted_answer=completed_sub_question.answer,
            performance=completed_sub_question.performance,
            feedback=completed_sub_question.feedback,
        )
        for completed_sub_question in completed_sub_questions
    ]


@router.get("/questions/completed", response_model=List[Question])
async def get_completed_questions(
    current_user: User = Depends(get_current_user),
):
    """Get all completed questions for the current user.

    Args:
        current_user (User): Current user from the token.

    Returns:
        List[Question]: A list of questions that the user has completed.
    """
    completed_sub_questions = await user_manager.get_completed_sub_questions(
        user_id=current_user.id
    )
    questions: Dict[int, DBQuestion] = {
        completed_sub_question.sub_question.question_id: completed_sub_question.sub_question.question
        for completed_sub_question in completed_sub_questions
    }
    questions_sub_questions: Dict[int, List[CompletedSubQuestion]] = defaultdict(list)
    for completed_sub_question in completed_sub_questions:
        questions_sub_questions[completed_sub_question.sub_question.question_id].append(
            completed_sub_question
        )

    # ensure unique sub_questions, older sub_questions are kept
    for question_id, sub_questions in questions_sub_questions.items():
        new_sub_questions: Dict[int, CompletedSubQuestion] = {}
        for sub_question in sub_questions:
            if sub_question.id not in new_sub_questions:
                new_sub_questions[sub_question.id] = sub_question
            else:
                if (
                    new_sub_questions[sub_question.id].created_at
                    < sub_question.created_at
                ):
                    new_sub_questions[sub_question.id] = sub_question
        questions_sub_questions[question_id] = list(new_sub_questions.values())

    return [
        Question(
            id=question.id,
            name=question.name,
            source=question.source,
            sub_questions=[
                SubQuestion(
                    id=sub_question.id,
                    description=sub_question.sub_question.description,
                    answer=sub_question.sub_question.answer,
                    concept=sub_question.sub_question.concept,
                    process=sub_question.sub_question.process,
                    keywords=sub_question.sub_question.keywords,
                    options=sub_question.sub_question.options,
                    image_id=sub_question.sub_question.image_id,
                    submitted_answer=sub_question.answer,
                    performance=sub_question.performance,
                    feedback=sub_question.feedback,
                )
                for sub_question in questions_sub_questions[question.id]
            ],
        )
        for question in questions.values()
    ]


@router.get("/question/completed", response_model=Question)
async def get_completed_question(
    question_id: int,
    current_user: User = Depends(get_current_user),
):
    """Get a completed question for the current user.

    Args:
        question_id (int): The ID of the question.
        current_user (User): Current user from the token.

    Raises:
        HTTPException: If the question is not found.

    Returns:
        Question: The completed question.
    """
    completed_sub_questions = await user_manager.get_completed_sub_questions(
        user_id=current_user.id
    )
    completed_sub_questions = [
        completed_sub_question
        for completed_sub_question in completed_sub_questions
        if completed_sub_question.sub_question.question_id == question_id
    ]

    if not completed_sub_questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed sub-questions found",
        )

    sub_questions: Dict[int, SubQuestion] = {}
    for completed_sub_question in completed_sub_questions:
        sub_questions[completed_sub_question.sub_question_id] = SubQuestion(
            id=completed_sub_question.sub_question_id,
            description=completed_sub_question.sub_question.description,
            answer=completed_sub_question.sub_question.answer,
            concept=completed_sub_question.sub_question.concept,
            process=completed_sub_question.sub_question.process,
            keywords=completed_sub_question.sub_question.keywords,
            options=completed_sub_question.sub_question.options,
            image_id=completed_sub_question.sub_question.image_id,
            submitted_answer=completed_sub_question.answer,
            performance=completed_sub_question.performance,
            feedback=completed_sub_question.feedback,
        )

    return Question(
        id=completed_sub_questions[0].sub_question.question_id,
        name=completed_sub_questions[0].sub_question.question.name,
        source=completed_sub_questions[0].sub_question.question.source,
        sub_questions=list(sub_questions.values()),
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
            question_ids=[question.id for question in assignment.questions],
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
                    question_ids=[question.id for question in assignment.questions],
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
                    question_ids=[
                        question.id for question in assignment.assignment.questions
                    ],
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


@router.get("/class/data", response_model=ClassData)
async def get_class_data(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get the data for the current user's class.

    Args:
        current_user (User): Current user from the token.

    Raises:
        HTTPException: If the user is not found or is not enrolled in a class.

    Returns:
        ClassData: The data for the current user's class.
    """
    user = await user_manager.get_user_by_id(user_id=current_user.id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.enrolled_class_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not enrolled in a class",
        )

    class_ = await user_manager.get_class_by_id(class_id=user.enrolled_class_id)
    assert class_ is not None

    teacher = await user_manager.get_user_by_id(user_id=class_.teacher_id)
    assert teacher is not None

    class_assignments = await user_manager.get_assignments_by_class_id(
        class_id=class_.id, user_id=user.id
    )

    to_do_assignments = []
    done_assignments = []
    for class_assignment in class_assignments:
        if await user_manager.is_assignment_completed(
            user_id=user.id, assignment_id=class_assignment.assignment.id
        ):
            done_assignments.append(
                Assignment(
                    id=class_assignment.assignment.id,
                    name=class_assignment.assignment.name,
                    description=class_assignment.assignment.description,
                    teacher_id=class_assignment.assignment.teacher_id,
                    question_ids=[
                        question.id
                        for question in class_assignment.assignment.questions
                    ],
                    due_date=class_assignment.due_date,
                )
            )
        else:
            to_do_assignments.append(
                Assignment(
                    id=class_assignment.assignment.id,
                    name=class_assignment.assignment.name,
                    description=class_assignment.assignment.description,
                    teacher_id=class_assignment.assignment.teacher_id,
                    question_ids=[
                        question.id
                        for question in class_assignment.assignment.questions
                    ],
                    due_date=class_assignment.due_date,
                )
            )

    return ClassData(
        class_name=class_.name,
        teacher_name=teacher.display_name,
        to_do_assignments=to_do_assignments,
        done_assignments=done_assignments,
    )
