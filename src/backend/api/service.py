import datetime
from typing import Optional
from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, HTTPException, Depends, status

from backend.db import user_manager
from backend.api.models.user import User
from backend.types.user import Permission
from backend.services.analyzer import Analyzer
from backend.exceptions.user import UserIdInvalid
from backend.api.base import get_current_user_generator
from backend.services.analyzer.models import (
    Performances,
    PerformancesData,
    PerformanceTrends,
)


router = APIRouter(prefix="/service", tags=["service"])
get_current_user = get_current_user_generator(
    OAuth2PasswordBearer(tokenUrl="../user/token")
)
analyzer = Analyzer(user_manager=user_manager)


@router.get("/get_performances", response_model=PerformancesData)
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


@router.get("/get_best_performances", response_model=Performances)
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


@router.get("/get_average_performances", response_model=Performances)
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


@router.get("/get_recent_best_performances", response_model=Performances)
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


@router.get("/get_recent_average_performances", response_model=Performances)
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


@router.get("/get_performance_trends", response_model=PerformanceTrends)
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
