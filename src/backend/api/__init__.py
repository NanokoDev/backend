from fastapi import APIRouter

from backend.api.question import router as question_router


router = APIRouter(prefix="/v1")
router.include_router(question_router)
