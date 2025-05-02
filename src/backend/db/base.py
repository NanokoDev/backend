from typing import Optional
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from backend.db.models.base import Base


class DatabaseManager:
    """A class to manage the database"""

    def __init__(self, path: Optional[str] = ":memory:"):
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{path}")
        self.Session: sessionmaker[AsyncSession] = sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init(self) -> None:
        """Initialise the database and create the tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        """Close the database connection"""
        self.Session.close_all()
