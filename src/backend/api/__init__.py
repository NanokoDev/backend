from fastapi import APIRouter, FastAPI
from contextlib import asynccontextmanager

from backend.config import config
from backend.types.user import Permission
from backend.api.user import user_manager
from backend.api.base import database_manager
from backend.api.bank import router as bank_router
from backend.api.user import router as user_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Lifespan context manager for bank API

    used to initialize and close the database connection
    """
    await database_manager.init()

    # Initialise admin account if it does not exist
    if not await user_manager.get_user_by_username(config.admin_username):
        await user_manager._create_user(
            username=config.admin_username,
            email=config.admin_email,
            display_name=config.admin_display_name,
            password=config.admin_password,
            permission=Permission.ADMIN,
        )
    yield
    await database_manager.close()


router = APIRouter(prefix="/v1", lifespan=lifespan)
router.include_router(bank_router)
router.include_router(user_router)
