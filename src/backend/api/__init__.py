from fastapi import APIRouter, FastAPI
from contextlib import asynccontextmanager

from backend.api.base import database_manager
from backend.api.bank import router as bank_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Lifespan context manager for bank API

    used to initialize and close the database connection
    """
    await database_manager.init()
    yield
    await database_manager.close()


router = APIRouter(prefix="/v1", lifespan=lifespan)
router.include_router(bank_router)
