from fastapi import APIRouter

from backend.api.bank import router as bank_router


router = APIRouter(prefix="/v1")
router.include_router(bank_router)
