import re
import bcrypt
import datetime
from sqlalchemy import select
from typing import Optional, List
from sqlalchemy.orm import joinedload

from backend.db.base import DatabaseManager
from backend.types.user import Permission, Performance
from backend.exceptions.bank import SubQuestionIdInvalid
from backend.db.models.bank import SubQuestion, Question
from backend.db.models.user import User, CompletedSubQuestion, Class, Assignment
from backend.exceptions.user import (
    UserIdInvalid,
    ClassIdInvalid,
    UserEmailInvalid,
    ClassAlreadyExists,
    AssignmentIdInvalid,
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
        user_id: int,
        sub_question_id: int,
        assignment_id: int,
        answer: str,
        performance: Performance,
        feedback: str = None,
    ) -> CompletedSubQuestion:
        """Add a completed sub-question for a user.

        Args:
            user_id (int): The ID of the user.
            sub_question_id (int): The ID of the sub-question.
            assignment_id (int): The ID of the assignment.
            answer (str): The answer provided by the user.
            performance (Performance): The performance level of the user on this sub-question.
            feedback (str, optional): Feedback for the user. Defaults to None.

        Raises:
            UserIdInvalid: If the user with the given ID is not found.
            AssignmentIdInvalid: If the assignment with the given ID is not found.
            PermissionError: If the user is not enrolled in any class.
            SubQuestionIdInvalid: If the sub-question with the given ID is not found.
            PermissionError: If the user does not have permission to complete this assignment.

        Returns:
            CompletedSubQuestion: The created completed sub-question object.
        """
        async with self._Session() as session:
            async with session.begin():
                user_result = await session.execute(
                    select(User)
                    .options(joinedload(User.enrolled_class))
                    .filter(User.id == user_id)
                )
                user = user_result.scalars().first()
                if user is None:
                    raise UserIdInvalid(user_id)

                assignment_result = await session.execute(
                    select(Assignment).filter(Assignment.id == assignment_id)
                )
                assignment = assignment_result.scalars().first()
                if assignment is None:
                    raise AssignmentIdInvalid(assignment_id)

                if user.enrolled_class_id is None:
                    raise PermissionError(
                        f"User {user.username} is not enrolled in any class."
                    )

                sub_question_result = await session.execute(
                    select(SubQuestion).filter(SubQuestion.id == sub_question_id)
                )
                sub_question = sub_question_result.scalars().first()
                if sub_question is None:
                    raise SubQuestionIdInvalid(sub_question_id)

                assignment_ids = [
                    assignment.id for assignment in user.enrolled_class.assignments
                ]
                if assignment.id not in assignment_ids:
                    raise PermissionError(
                        f"User {user.username} is not allowed to complete this assignment."
                    )

                completed_sub_question = CompletedSubQuestion(
                    user_id=user.id,
                    sub_question_id=sub_question.id,
                    assignment_id=assignment.id,
                    answer=answer,
                    performance=performance,
                    feedback=feedback,
                )
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
                    name=class_name, teacher_id=teacher_id, enter_code=enter_code
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

    async def create_assignment(
        self,
        teacher_id: int,
        assignment_name: str,
        assignment_description: str,
        due_date: datetime.datetime,
        questions: List[Question],
    ) -> Assignment:
        """Create a new assignment for a teacher.

        Args:
            teacher_id (int): The ID of the teacher.
            assignment_name (str): The name of the assignment.
            assignment_description (str): The description of the assignment.
            due_date (datetime.datetime): The due date of the assignment.
            questions (List[Question]): The list of questions for the assignment.

        Raises:
            UserIdInvalid: If the teacher with the given ID is not found.
            PermissionError: If the user does not have permission to create an assignment.

        Returns:
            Assignment: The created assignment object.
        """
        async with self._Session() as session:
            async with session.begin():
                teacher = await self.get_user_by_id(teacher_id)
                if teacher is None:
                    raise UserIdInvalid(teacher_id)

                if teacher.permission < Permission.TEACHER:
                    raise PermissionError(
                        f"User {teacher.username} does not have permission to create an assignment."
                    )

                assignment = Assignment(
                    name=assignment_name,
                    description=assignment_description,
                    due_date=due_date,
                    teacher_id=teacher_id,
                )
                assignment.questions.extend(questions)
                session.add(assignment)
                return assignment

    async def assign_assignment_to_class(
        self, assignment_id: int, class_id: int, teacher_id: int
    ) -> None:
        """Assign an assignment to a class.

        Args:
            assignment_id (int): The ID of the assignment.
            class_id (int): The ID of the class.
            teacher_id (int): The ID of the teacher.

        Raises:
            AssignmentIdInvalid: If the assignment with the given ID is not found.
            PermissionError: If the user does not have permission to assign this assignment.
            ClassIdInvalid: If the class with the given ID is not found.

        Returns:
            None: The assignment has been successfully assigned to the class.
        """
        async with self._Session() as session:
            async with session.begin():
                assignment_result = await session.execute(
                    select(Assignment).filter(Assignment.id == assignment_id)
                )
                assignment = assignment_result.scalars().first()
                if assignment is None:
                    raise AssignmentIdInvalid(assignment_id)

                if assignment.teacher_id != teacher_id:
                    raise PermissionError(
                        f"User {teacher_id} does not have permission to assign this assignment."
                    )

                class_result = await session.execute(
                    select(Class).filter(Class.id == class_id)
                )
                class_ = class_result.scalars().first()
                if class_ is None:
                    raise ClassIdInvalid(class_id)

                class_.assignments.append(assignment)
                return None

    async def get_assignments_by_teacher_id(self, teacher_id: int) -> List[Assignment]:
        """Get all assignments created by a teacher.

        Args:
            teacher_id (int): The ID of the teacher.

        Raises:
            UserIdInvalid: If the teacher with the given ID is not found.
            PermissionError: If the user does not have permission to view assignments.

        Returns:
            List[Assignment]: A list of assignments created by the teacher.
        """
        async with self._Session() as session:
            teacher_result = await session.execute(
                select(User).filter(User.id == teacher_id)
            )
            teacher = teacher_result.scalars().first()
            if teacher is None:
                raise UserIdInvalid(teacher_id)

            if teacher.permission < Permission.TEACHER:
                raise PermissionError(
                    f"User {teacher.username} does not have permission to view assignments."
                )

            return teacher.assignments

    async def get_assignments_by_class_id(
        self, class_id: int, user_id: int
    ) -> List[Assignment]:
        """Get all assignments for a class.

        Args:
            class_id (int): The ID of the class.
            user_id (int): The ID of the user.

        Raises:
            ClassIdInvalid: If the class with the given ID is not found.
            UserIdInvalid: If the user with the given ID is not found.
            PermissionError: If the user is not enrolled in the class or is the teacher of the class.

        Returns:
            List[Assignment]: A list of assignments for the class.
        """
        class_ = await self.get_class_by_id(class_id)
        if class_ is None:
            raise ClassIdInvalid(class_id)

        user = await self.get_user_by_id(user_id)
        if user is None:
            raise UserIdInvalid(user_id)

        if user.permission < Permission.ADMIN and (
            user.enrolled_class_id != class_id or class_.teacher_id == user.id
        ):
            raise PermissionError(
                f"User {user.id} is not enrolled in class {class_.id} or is the teacher of the class."
            )

        return class_.assignments

    async def get_assignments_by_student_id(self, student_id: int) -> List[Assignment]:
        """Get all assignments for a student.

        Args:
            student_id (int): The ID of the student.

        Raises:
            UserIdInvalid: If the student with the given ID is not found.

        Returns:
            List[Assignment]: A list of assignments for the student.
        """
        async with self._Session() as session:
            student_result = await session.execute(
                select(User)
                .options(joinedload(User.enrolled_class))
                .filter(User.id == student_id)
            )
            student = student_result.scalars().first()
            if student is None:
                raise UserIdInvalid(student_id)

            return (
                [assignment for assignment in student.enrolled_class.assignments]
                if student.enrolled_class
                else []
            )
