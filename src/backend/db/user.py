import re
import bcrypt
from sqlalchemy import select
from typing import Optional, List
from sqlalchemy.orm import joinedload

from backend.db.base import DatabaseManager
from backend.db.models.bank import SubQuestion
from backend.types.user import Permission, Performance
from backend.db.models.user import User, CompletedSubQuestion, Class
from backend.exceptions.user import (
    UserIdInvalid,
    ClassIdInvalid,
    UserEmailInvalid,
    ClassAlreadyExists,
    UsernameAlreadyExists,
    UserEmailAlreadyExists,
    ClassEnterCodeIncorrect,
)


class UserManager:
    """A class to manage user-related database operations."""

    def __init__(self, database_manager: DatabaseManager):
        self._Session = database_manager.Session

    async def create_user(
        self,
        username: str,
        email: str,
        display_name: str,
        password: str,
        permission: Permission,
    ) -> User:
        """Create a new user.

        Args:
            username (str): The username of the user.
            email (str): The email of the user.
            display_name (str): The display name of the user.
            password (str): The password of the user.
            permission (Permission): The permission level of the user.

        Raises:
            UserEmailInvalid: If the email format is invalid.
            UserEmailAlreadyExists: If the email already exists in the database.
            UsernameAlreadyExists: If the username already exists in the database.

        Returns:
            User: The created user object.
        """
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt).decode()

        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, email):
            raise UserEmailInvalid(email)

        existing_user = await self.get_user_by_email(email)
        if existing_user:
            raise UserEmailAlreadyExists(email)

        existing_user = await self.get_user_by_username(username)
        if existing_user:
            raise UsernameAlreadyExists(username)

        user = User(
            username=username,
            email=email,
            display_name=display_name,
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

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by their email.

        Args:
            email (str): The email of the user.

        Returns:
            Optional[User]: The user object if found, otherwise None.
        """
        async with self._Session() as session:
            user_result = await session.execute(
                select(User).filter(User.email == email)
            )
            user = user_result.scalars().first()
            return user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by their username.

        Args:
            username (str): The username of the user.

        Returns:
            Optional[User]: The user object if found, otherwise None.
        """
        async with self._Session() as session:
            user_result = await session.execute(
                select(User).filter(User.username == username)
            )
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
        feedback: str = None,
    ) -> CompletedSubQuestion:
        """Add a completed sub-question for a user.

        Args:
            user (User): The user object.
            sub_question (SubQuestion): The sub-question object.
            answer (str): The answer provided by the user.
            performance (Performance): The performance level of the user on this sub-question.
            feedback (str, optional): Feedback for the user. Defaults to None.

        Returns:
            CompletedSubQuestion: The created completed sub-question object.
        """
        completed_sub_question = CompletedSubQuestion(
            user=user,
            sub_question=sub_question,
            answer=answer,
            performance=performance,
            feedback=feedback,
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

    async def create_class(
        self, teacher_id: int, class_name: str, enter_code: str
    ) -> Class:
        """Create a new class for a teacher.

        Args:
            teacher_id (int): The ID of the teacher.
            class_name (str): The name of the class.
            enter_code (str): The enter code that students will use to join the class.

        Raises:
            UserIdInvalid: If the teacher with the given ID is not found.
            PermissionError: If the user does not have permission to create a class.
            ClassAlreadyExists: If the class name already exists.

        Returns:
            Class: The created class object.
        """
        async with self._Session() as session:
            async with session.begin():
                teacher = await self.get_user_by_id(teacher_id)
                if teacher is None:
                    raise UserIdInvalid(teacher_id)
                if teacher.permission < Permission.TEACHER:
                    raise PermissionError(
                        f"User {teacher.username} does not have permission to create a class."
                    )

                existing_class = await session.execute(
                    select(Class).filter(Class.name == class_name)
                )
                if existing_class.scalars().first() is not None:
                    raise ClassAlreadyExists(class_name)

                new_class = Class(
                    name=class_name, teacher=teacher, enter_code=enter_code
                )
                session.add(new_class)
                return new_class

    async def join_class(self, user_id: int, class_id: int, enter_code: str) -> Class:
        """Join a user to a class.

        Args:
            user_id (int): ID of the user.
            class_id (int): ID of the class.
            enter_code (str): The enter code for the class.

        Raises:
            UserIdInvalid: If the user with the given ID is not found.
            PermissionError: If the user was already enrolled in a class.
            ClassIdInvalid: If the class with the given ID is not found.
            PermissionError: If the user is trying to join their own class.
            ClassEnterCodeIncorrect: If the enter code is incorrect.

        Returns:
            Class: The class object the user joined.
        """
        async with self._Session() as session:
            async with session.begin():
                user = await self.get_user_by_id(user_id)
                if user is None:
                    raise UserIdInvalid(user_id)

                if user.enrolled_class_id is not None:
                    raise PermissionError(
                        f"User {user.username} is already enrolled in a class."
                    )

                class_ = await session.execute(
                    select(Class).filter(Class.id == class_id)
                )
                class_ = class_.scalars().first()
                if class_ is None:
                    raise ClassIdInvalid(class_id)

                if class_.teacher_id == user.id:
                    raise PermissionError(
                        f"User {user.username} cannot join their own class."
                    )

                if class_.enter_code != enter_code:
                    raise ClassEnterCodeIncorrect(enter_code)

                class_.students.append(user)
                user.enrolled_class = class_
                return class_

    async def leave_class(self, user_id: int) -> None:
        """Leave the class the user is enrolled in.

        Args:
            user_id (int): ID of the user.

        Raises:
            UserIdInvalid: If the user with the given ID is not found.
            PermissionError: If the user is not enrolled in any class.

        Returns:
            None: The user has successfully left the class.
        """
        async with self._Session() as session:
            async with session.begin():
                user = await self.get_user_by_id(user_id)
                if user is None:
                    raise UserIdInvalid(user_id)

                if user.enrolled_class_id is None:
                    raise PermissionError(
                        f"User {user.username} is not enrolled in any class."
                    )

                user.enrolled_class = None
                user.enrolled_class_id = None
                return None

    async def get_class_by_id(self, class_id: int) -> Optional[Class]:
        """Get a class by its ID.


        Args:
            class_id (int): The ID of the class.

        Returns:
            Optional[Class]: The class object if found, otherwise None.
        """
        async with self._Session() as session:
            class_result = await session.execute(
                select(Class).filter(Class.id == class_id)
            )
            class_ = class_result.scalars().first()
            return class_

    async def get_class_by_name(self, class_name: str) -> Optional[Class]:
        """Get a class by its name

        Args:
            class_name (str): The name of the class.

        Returns:
            Optional[Class]: The class object if found, otherwise None.
        """
        async with self._Session() as session:
            class_result = await session.execute(
                select(Class).filter(Class.name == class_name)
            )
            class_ = class_result.scalars().first()
            return class_
