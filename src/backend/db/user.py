import bcrypt
from sqlalchemy import select
from typing import Optional, List
from sqlalchemy.orm import joinedload

from backend.db.base import DatabaseManager
from backend.db.models.bank import SubQuestion
from backend.exceptions.user import UserIdInvalid
from backend.types.user import Permission, Performance
from backend.db.models.user import User, CompletedSubQuestion


class UserManager:
    """A class to manage user-related database operations."""

    def __init__(self, database_manager: DatabaseManager):
        self._Session = database_manager.Session

    async def create_user(
        self, name: str, password: str, permission: Permission
    ) -> User:
        """Create a new user.

        Args:
            name (str): The name of the user.
            password (str): The password of the user, which will be hashed and salted before storage.
            permission (Permission): The permission of the user.

        Returns:
            User: The created user object.
        """
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt).decode()
        user = User(
            name=name,
            password_hash=hashed_password,
            permission=permission,
        )
        async with self._Session() as session:
            async with session.begin():
                session.add(user)
        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by their ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            Optional[User]: The user object if found, otherwise None.
        """
        async with self._Session() as session:
            user_result = await session.execute(select(User).filter(User.id == user_id))
            user = user_result.scalars().first()
            return user

    async def is_correct_password(self, user_id: int, password: str) -> bool:
        """Check if the provided password matches the stored password for the user.

        Args:
            user_id (int): The ID of the user.
            password (str): The password to check.

        Raises:
            UserIdInvalid: If the user with the given ID is not found.

        Returns:
            bool: True if the password is correct, False otherwise.
        """
        user = await self.get_user_by_id(user_id)
        if user is None:
            raise UserIdInvalid(user_id)
        return bcrypt.checkpw(password.encode(), user.password_hash.encode())

    async def add_completed_sub_question(
        self,
        user: User,
        sub_question: SubQuestion,
        answer: str,
        performance: Performance,
    ) -> CompletedSubQuestion:
        """Add a completed sub-question for a user.

        Args:
            user (User): The user object.
            sub_question (SubQuestion): The sub-question object.
            answer (str): The answer provided by the user.
            performance (Performance): The performance level of the user on this sub-question.

        Returns:
            CompletedSubQuestion: The created completed sub-question object.
        """
        completed_sub_question = CompletedSubQuestion(
            user=user,
            sub_question=sub_question,
            answer=answer,
            performance=performance,
        )
        async with self._Session() as session:
            async with session.begin():
                session.add(completed_sub_question)
        return completed_sub_question

    async def get_completed_sub_questions(
        self, user_id: int
    ) -> List[CompletedSubQuestion]:
        """Get all completed sub-questions of a user.

        Args:
            user_id (int): The ID of the user.

        Raises:
            UserIdInvalid: If the user with the given ID is not found.

        Returns:
            List[CompletedSubQuestion]: A list of completed sub-questions for the user.
        """
        async with self._Session() as session:
            user_result = await session.execute(
                select(User)
                .options(joinedload(User.completed_sub_questions))
                # eager load sub_questions to prevent sqlalchemy.orm.exc.DetachedInstanceError
                .filter(User.id == user_id)
            )
            user = user_result.scalars().first()

            if user is None:
                raise UserIdInvalid(user_id)

            return user.completed_sub_questions

    async def reset_password(self, user_id: int, new_password: str) -> User:
        """Reset the password of a user.

        Args:
            user_id (int): The ID of the user.
            new_password (str): The new password to set for the user.

        Raises:
            UserIdInvalid: If the user with the given ID is not found.

        Returns:
            User: The updated user object with the new password.
        """
        async with self._Session() as session:
            async with session.begin():
                user_result = await session.execute(
                    select(User).filter(User.id == user_id)
                )
                user = user_result.scalars().first()
                if user is None:
                    raise UserIdInvalid(user_id)

                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(new_password.encode(), salt).decode()
                user.password_hash = hashed_password
