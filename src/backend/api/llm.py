from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, Depends, HTTPException, status

from backend.db import llm_manager
from backend.api.models.user import User
from backend.types.user import Permission
from backend.exceptions.llm import LLMRequestError
from backend.api.base import get_current_user_generator
from backend.exceptions.bank import SubQuestionIdInvalid


router = APIRouter(prefix="/llm", tags=["llm"])
get_current_user = get_current_user_generator(
    OAuth2PasswordBearer(tokenUrl="../user/token")
)


@router.get("/get_hint")
async def get_hint(
    sub_question_id: int,
    question: str,
    user: User = Depends(get_current_user),
) -> str:
    if user.permission < Permission.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )

    try:
        hint = await llm_manager.get_hint(
            sub_question_id=sub_question_id, question=question
        )
        return JSONResponse({"hint": hint}, status_code=status.HTTP_200_OK)
    except LLMRequestError:
        # TODO: log the error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM request error",
        )
    except SubQuestionIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sub-question not found: {sub_question_id}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )
