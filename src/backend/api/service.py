import random
import datetime
from typing import Optional, List
from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, HTTPException, Depends, status

from backend.types.user import Permission
from backend.db import user_manager, analyzer
from backend.db.models.user import User as DBUser
from backend.exceptions.user import UserIdInvalid
from backend.api.models.user import User, Assignment
from backend.api.base import get_current_user_generator
from backend.api.models.service import Overview, TeacherOverview, ClassCard
from backend.services.analyzer.models import (
    Performances,
    PerformancesData,
    PerformanceTrends,
    PerformanceDateData,
)


router = APIRouter(prefix="/service", tags=["service"])
get_current_user = get_current_user_generator(
    OAuth2PasswordBearer(tokenUrl="../user/token")
)


@router.get("/performances", response_model=PerformancesData)
async def get_performances(
    user_id: int,
    user: User = Depends(get_current_user),
):
    """Get the performance of a user.

    Args:
        user_id (int): The id of the user to get the performance for.
        user (User, optional): The user object Defaults to Depends(get_current_user).

    Raises:
        HTTPException: 403 forbidden if the user does not have permission.
        HTTPException: 404 not found if the user is not found.
        HTTPException: 500 internal server error if there is an unexpected error.

    Returns:
        PerformancesData: The performance data of the user.
    """
    if user.permission < Permission.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )

    try:
        if not await user_manager.is_my_student(teacher_id=user.id, student_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )

    try:
        performances = await analyzer.get_performances(user_id=user_id)
        return performances
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get("/performances/best", response_model=Performances)
async def get_best_performances(
    user_id: int,
    user: User = Depends(get_current_user),
):
    """Get the best performance of a user.

    Args:
        user_id (int): The id of the user to get the performance for.
        user (User, optional): The user object. Defaults to Depends(get_current_user).

    Raises:
        HTTPException: 403 forbidden if the user does not have permission.
        HTTPException: 404 not found if the user is not found.
        HTTPException: 500 internal server error if there is an unexpected error.

    Returns:
        Performances: The best performance data of the user.
    """
    if user.permission < Permission.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )

    try:
        if not await user_manager.is_my_student(teacher_id=user.id, student_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )

    try:
        performances = await analyzer.get_best_performances(user_id=user_id)
        return performances
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get("/performances/average", response_model=Performances)
async def get_average_performances(
    user_id: int,
    user: User = Depends(get_current_user),
):
    """Get the average performance of a user.

    Args:
        user_id (int): The id of the user to get the performance for.
        user (User, optional): The user object. Defaults to Depends(get_current_user).

    Raises:
        HTTPException: 403 forbidden if the user does not have permission.
        HTTPException: 404 not found if the user is not found.
        HTTPException: 500 internal server error if there is an unexpected error.

    Returns:
        Performances: The average performance data of the user.
    """
    if user.permission < Permission.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )

    try:
        if not await user_manager.is_my_student(teacher_id=user.id, student_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )

    try:
        performances = await analyzer.get_average_performances(user_id=user_id)
        return performances
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get("/performances/best/recent", response_model=Performances)
async def get_recent_best_performances(
    user_id: int,
    start_time: datetime.datetime,
    user: User = Depends(get_current_user),
):
    """Get the recent best performance of a user.

    Args:
        user_id (int): The id of the user to get the performance for.
        start_time (datetime.datetime): The start time to get the performance from.
        user (User, optional): The user object. Defaults to Depends(get_current_user).

    Raises:
        HTTPException: 403 forbidden if the user does not have permission.
        HTTPException: 404 not found if the user is not found.
        HTTPException: 500 internal server error if there is an unexpected error.

    Returns:
        Performances: The recent best performance data of the user.
    """
    if user.permission < Permission.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )

    try:
        if not await user_manager.is_my_student(teacher_id=user.id, student_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )

    try:
        timedelta = datetime.datetime.now(datetime.timezone.utc) - start_time
        performances = await analyzer.get_recent_best_performances(
            user_id=user_id, timedelta=timedelta
        )
        return performances
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get("/performances/average/recent", response_model=Performances)
async def get_recent_average_performances(
    user_id: int,
    start_time: datetime.datetime,
    user: User = Depends(get_current_user),
):
    """Get the recent average performance of a user.

    Args:
        user_id (int): The id of the user to get the performance for.
        start_time (datetime.datetime): The start time to get the performance from.
        user (User, optional): The user object. Defaults to Depends(get_current_user).

    Raises:
        HTTPException: 403 forbidden if the user does not have permission.
        HTTPException: 404 not found if the user is not found.
        HTTPException: 500 internal server error if there is an unexpected error.

    Returns:
        Performances: The recent average performance data of the user.
    """
    if user.permission < Permission.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )

    try:
        if not await user_manager.is_my_student(teacher_id=user.id, student_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )

    try:
        timedelta = datetime.datetime.now(datetime.timezone.utc) - start_time
        performances = await analyzer.get_recent_average_performances(
            user_id=user_id, timedelta=timedelta
        )
        return performances
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get("/performances/trends", response_model=PerformanceTrends)
async def get_performance_trends(
    user_id: int,
    start_time: Optional[datetime.datetime] = None,
    user: User = Depends(get_current_user),
):
    """Get the performance trends of a user.

    Args:
        user_id (int): The id of the user to get the performance trends for.
        start_time (Optional[datetime.datetime], optional): The start time to get the performance trends from. Defaults to None.
        user (User, optional): The user object. Defaults to Depends(get_current_user).

    Raises:
        HTTPException: 403 forbidden if the user does not have permission.
        HTTPException: 404 not found if the user is not found.
        HTTPException: 500 internal server error if there is an unexpected error.

    Returns:
        PerformanceTrends: The performance trends data of the user.
    """
    if user.permission < Permission.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )

    try:
        if not await user_manager.is_my_student(teacher_id=user.id, student_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )
    try:
        performance_trends = (
            (await analyzer.get_performance_trends(user_id=user_id))
            if start_time is None
            else (
                await analyzer.get_performance_trends(
                    user_id=user_id,
                    timedelta=datetime.datetime.now(datetime.timezone.utc) - start_time,
                )
            )
        )
        return performance_trends
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get("/performances/date", response_model=PerformanceDateData)
async def get_performance_date_data(
    user_id: int,
    start_time: Optional[datetime.datetime] = None,
    user: User = Depends(get_current_user),
):
    """Get the performance date data of a user.

    Args:
        user_id (int): The id of the user to get the performance date data for.
        start_time (Optional[datetime.datetime], optional): The start time to get the performance date data from. Defaults to None.
        user (User, optional): The user object. Defaults to Depends(get_current_user).

    Raises:
        HTTPException: 403 forbidden if the user does not have permission.
        HTTPException: 404 not found if the user is not found.
        HTTPException: 500 internal server error if there is an unexpected error.

    Returns:
        PerformanceDateData: The performance date data of the user.
    """

    if user.permission < Permission.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )

    try:
        if not await user_manager.is_my_student(teacher_id=user.id, student_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
    except UserIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )

    try:
        timedelta = (
            datetime.datetime.now(datetime.timezone.utc) - start_time
            if start_time is not None
            else None
        )
        performance_date_data = await analyzer.get_performance_date_data(
            user_id=user_id, timedelta=timedelta
        )
        return performance_date_data
    except TypeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time requires timezone information",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get("/overview", response_model=Overview)
async def get_overview(current_user: User = Depends(get_current_user)):
    """Get the overview of the current user.

    Args:
        current_user (User, optional): Current user from the token. Defaults to Depends(get_current_user).

    Raises:
        HTTPException: If the user is not found or is not enrolled in a class.

    Returns:
        Overview: The overview of the current user.
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

    class_ = await user_manager.get_class_by_id(user.enrolled_class_id)
    assert class_ is not None

    class_assignments = await user_manager.get_assignments_by_student_id(user.id)
    timedelta = datetime.timedelta(days=30)
    performances = await analyzer.get_recent_average_performances(
        user_id=user.id, timedelta=timedelta
    )

    completed_sub_questions = await user_manager.get_completed_sub_questions(user.id)

    return Overview(
        class_name=class_.name,
        assignments=[
            Assignment(
                id=class_assignment.assignment.id,
                name=class_assignment.assignment.name,
                description=class_assignment.assignment.description,
                teacher_id=class_assignment.assignment.teacher_id,
                question_ids=[
                    question.id for question in class_assignment.assignment.questions
                ],
                due_date=class_assignment.due_date,
            )
            for class_assignment in class_assignments
        ],
        display_name=user.display_name,
        total_question_number=len(completed_sub_questions),
        performances=performances,
    )


@router.get("/overview/teacher", response_model=TeacherOverview)
async def get_teacher_overview(current_user: User = Depends(get_current_user)):
    """Get the overview of the current user.

    Args:
        current_user (User, optional): Current user from the token. Defaults to Depends(get_current_user).

    Raises:
        HTTPException: If the user is not found or is not a teacher.

    Returns:
        TeacherOverview: The overview of the current user.
    """
    user = await user_manager.get_user_by_id(user_id=current_user.id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.permission < Permission.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )

    classes = await user_manager.get_teaching_classes(user.id)
    class_cards: List[ClassCard] = []
    students: List[DBUser] = []

    for class_ in classes:
        class_cards.append(
            ClassCard(
                class_id=class_.id,
                name=class_.name,
                student_number=len(class_.students),
                assignments=[
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
                    for class_assignment in class_.class_assignments
                ],
            )
        )
        students.extend(class_.students)

    assignments = await user_manager.get_assignments_by_teacher_id(user.id)

    return TeacherOverview(
        classes=class_cards,
        assignments=[
            Assignment(
                id=assignment.id,
                name=assignment.name,
                description=assignment.description,
                teacher_id=assignment.teacher_id,
                question_ids=[question.id for question in assignment.questions],
            )
            for assignment in assignments
        ],
        students=[
            User(
                id=student.id,
                name=student.username,
                display_name=student.display_name,
                email=student.email,
                permission=student.permission,
            )
            for student in (
                random.sample(students, k=5) if len(students) > 5 else students
            )
        ],
    )
