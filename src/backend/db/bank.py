from pathlib import Path
from sqlalchemy import or_
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import Optional, Union, List

from backend.db.models.user import User
from backend.db.base import DatabaseManager
from backend.exceptions.user import UserIdInvalid
from backend.types.question import ConceptType, ProcessType
from backend.db.models.bank import Image, SubQuestion, Question
from backend.exceptions.bank import (
    ImageIdInvalid,
    QuestionIdInvalid,
    SubQuestionIdInvalid,
)


class QuestionManager:
    """A class to manage the question bank database"""

    def __init__(self, database_manager: DatabaseManager):
        self._Session = database_manager.Session

    async def add_image(
        self, description: str, path: Union[str, Path], uploader_id: int
    ) -> Image:
        """Add an image to the database

        Args:
            description (str): The description of the image
            path (Union[str, Path]): The path to the image file
            uploader_id (int): The ID of the user who uploaded the image

        Returns:
            Image: The image object that was added to the database
        """
        async with self._Session() as session:
            async with session.begin():
                user_result = await session.execute(
                    select(User).filter(User.id == uploader_id)
                )
                user = user_result.scalars().first()
                image = Image(
                    description=description, path=str(path), uploader_id=uploader_id
                )
                image.uploader = user
                session.add(image)
                # session.begin().close will do session.commit() or rollback automatically
        return image

    async def add_sub_question(
        self,
        seq_number: int,
        description: str,
        answer: str,
        concept: ConceptType,
        process: ProcessType,
        options: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
    ) -> SubQuestion:
        """Add a subquestion to the database

        Args:
            seq_number (int): The number that will be used to sort subquestions
            description (str): The description of the subquestion
            answer (str): The answer to the subquestion
            concept (ConceptType): Subquestion's concept type
            process (ProcessType): Subquestion's process type
            options (List[str], optional): The options of the subquestion
            keywords (List[str], optional): The keywords of the subquestion

        Returns:
            SubQuestion: The subquestion object that was added to the database
        """

        sub_question = SubQuestion(
            seq_number=seq_number,
            description=description,
            answer=answer,
            concept=concept,
            process=process,
            options=options,
            keywords=keywords,
        )

        async with self._Session() as session:
            async with session.begin():
                session.add(sub_question)
        return sub_question

    async def add_question(self, name: str, source: str, uploader_id: int) -> Question:
        """Add a question to the database

        Args:
            name (str): The name of the question
            source (str): The source of the question
            uploader_id (int): The ID of the user who uploaded the question

        Raises:
            UserIdInvalid: If the user ID is invalid

        Returns:
            Question: The question object that was added to the database
        """

        async with self._Session() as session:
            async with session.begin():
                user_result = await session.execute(
                    select(User).filter(User.id == uploader_id)
                )
                user = user_result.scalars().first()
                if user is None:
                    raise UserIdInvalid(uploader_id)

                question = Question(
                    name=name,
                    source=source,
                    is_audited=False,
                    uploader_id=uploader_id,
                )
                question.uploader = user
                session.add(question)
        return question

    async def set_sub_question_image(self, sub_question_id: int, image_id: int) -> None:
        """Set the image for a subquestion

        Args:
            sub_question_id (int): The ID of the subquestion
            image_id (int): The ID of the image

        Raises:
            SubQuestionIdInvalid: If the subquestion ID is invalid
            ImageIdInvalid: If the image ID is invalid
        """
        async with self._Session() as session:
            async with session.begin():
                sub_question_result = await session.execute(
                    select(SubQuestion).filter(SubQuestion.id == sub_question_id)
                )
                sub_question = sub_question_result.scalars().first()

                if sub_question is None:
                    raise SubQuestionIdInvalid(sub_question_id)

                image_result = await session.execute(
                    select(Image).filter(Image.id == image_id)
                )
                image = image_result.scalars().first()

                if image is None:
                    raise ImageIdInvalid(image_id)

                sub_question.image_id = image.id

    async def delete_sub_question_image(self, sub_question_id: int) -> None:
        """Delete the image for a subquestion

        Args:
            sub_question_id (int): The ID of the subquestion

        Raises:
            SubQuestionIdInvalid: If the subquestion ID is invalid
        """
        async with self._Session() as session:
            async with session.begin():
                sub_question_result = await session.execute(
                    select(SubQuestion).filter(SubQuestion.id == sub_question_id)
                )
                sub_question = sub_question_result.scalars().first()

                if sub_question is None:
                    raise SubQuestionIdInvalid(sub_question_id)

                sub_question.image_id = None

    async def set_question(self, sub_question_ids: List[int], question_id: int) -> None:
        """Set subquestions for a question

        Args:
            sub_question_ids (List[int]): The IDs of the subquestions. The order matters.
            question_id (int): The ID of the question

        Raises:
            SubQuestionIdInvalid: If the subquestion ID is invalid
            QuestionIdInvalid: If the question ID is invalid
        """
        async with self._Session() as session:
            async with session.begin():
                sub_question_result = await session.execute(
                    select(SubQuestion).filter(SubQuestion.id.in_(sub_question_ids))
                )
                sub_questions = sub_question_result.scalars().all()

                if len(sub_questions) != len(sub_question_ids):
                    for i in range(len(sub_questions)):
                        if sub_questions[i].id != sub_question_ids[i]:
                            raise SubQuestionIdInvalid(sub_question_ids[i])

                question_result = await session.execute(
                    select(Question).filter(Question.id == question_id)
                )
                question = question_result.scalars().first()

                if question is None:
                    raise QuestionIdInvalid(question_id)

                for sub_question in sub_questions:
                    sub_question.question_id = question.id

    async def set_sub_question_description(
        self, sub_question_id: int, description: str
    ) -> None:
        """Set the description for a subquestion

        Args:
            sub_question_id (int): The ID of the subquestion
            description (str): The new description for the subquestion

        Raises:
            SubQuestionIdInvalid: If the subquestion ID is invalid
        """
        async with self._Session() as session:
            async with session.begin():
                sub_question_result = await session.execute(
                    select(SubQuestion).filter(SubQuestion.id == sub_question_id)
                )
                sub_question = sub_question_result.scalars().first()

                if sub_question is None:
                    raise SubQuestionIdInvalid(sub_question_id)

                sub_question.description = description

    async def set_sub_question_options(
        self, sub_question_id: int, options: List[str]
    ) -> None:
        """Set the options for a subquestion

        Args:
            sub_question_id (int): The ID of the subquestion
            options (List[str]): The new options for the subquestion

        Raises:
            SubQuestionIdInvalid: If the subquestion ID is invalid
        """
        async with self._Session() as session:
            async with session.begin():
                sub_question_result = await session.execute(
                    select(SubQuestion).filter(SubQuestion.id == sub_question_id)
                )
                sub_question = sub_question_result.scalars().first()

                if sub_question is None:
                    raise SubQuestionIdInvalid(sub_question_id)

                sub_question.options = options

    async def set_sub_question_answer(self, sub_question_id: int, answer: str) -> None:
        """Set the answer for a subquestion

        Args:
            sub_question_id (int): The ID of the subquestion
            answer (str): The new answer for the subquestion

        Raises:
            SubQuestionIdInvalid: If the subquestion ID is invalid
        """
        async with self._Session() as session:
            async with session.begin():
                sub_question_result = await session.execute(
                    select(SubQuestion).filter(SubQuestion.id == sub_question_id)
                )
                sub_question = sub_question_result.scalars().first()

                if sub_question is None:
                    raise SubQuestionIdInvalid(sub_question_id)

                sub_question.answer = answer

    async def set_sub_question_concept(
        self, sub_question_id: int, concept: ConceptType
    ) -> None:
        """Set the concept for a subquestion

        Args:
            sub_question_id (int): The ID of the subquestion
            concept (ConceptType): The new concept for the subquestion

        Raises:
            SubQuestionIdInvalid: If the subquestion ID is invalid
        """
        async with self._Session() as session:
            async with session.begin():
                sub_question_result = await session.execute(
                    select(SubQuestion).filter(SubQuestion.id == sub_question_id)
                )
                sub_question = sub_question_result.scalars().first()

                if sub_question is None:
                    raise SubQuestionIdInvalid(sub_question_id)

                sub_question.concept = concept

    async def set_sub_question_process(
        self, sub_question_id: int, process: ProcessType
    ) -> None:
        """Set the process for a subquestion

        Args:
            sub_question_id (int): The ID of the subquestion
            process (ProcessType): The new process for the subquestion

        Raises:
            SubQuestionIdInvalid: If the subquestion ID is invalid
        """
        async with self._Session() as session:
            async with session.begin():
                sub_question_result = await session.execute(
                    select(SubQuestion).filter(SubQuestion.id == sub_question_id)
                )
                sub_question = sub_question_result.scalars().first()

                if sub_question is None:
                    raise SubQuestionIdInvalid(sub_question_id)

                sub_question.process = process

    async def set_sub_question_keywords(
        self, sub_question_id: int, keywords: List[str]
    ) -> None:
        """Set the keywords for a subquestion

        Args:
            sub_question_id (int): The ID of the subquestion
            keywords (List[str]): The new keywords for the subquestion

        Raises:
            SubQuestionIdInvalid: If the subquestion ID is invalid
        """
        async with self._Session() as session:
            async with session.begin():
                sub_question_result = await session.execute(
                    select(SubQuestion).filter(SubQuestion.id == sub_question_id)
                )
                sub_question = sub_question_result.scalars().first()

                if sub_question is None:
                    raise SubQuestionIdInvalid(sub_question_id)

                sub_question.keywords = keywords

    async def set_question_name(self, question_id: int, name: str) -> None:
        """Set the name for a question

        Args:
            question_id (int): The ID of the question
            name (str): The new name for the question

        Raises:
            QuestionIdInvalid: If the question ID is invalid
        """
        async with self._Session() as session:
            async with session.begin():
                question_result = await session.execute(
                    select(Question).filter(Question.id == question_id)
                )
                question = question_result.scalars().first()

                if question is None:
                    raise QuestionIdInvalid(question_id)

                question.name = name

    async def is_image_uploader(self, image_id: int, user_id: int) -> bool:
        """Check if a user is the uploader of an image

        Args:
            image_id (int): The ID of the image
            user_id (int): The ID of the user

        Raises:
            ImageIdInvalid: If the image ID is invalid

        Returns:
            bool: True if the user is the uploader of the image, False otherwise
        """
        async with self._Session() as session:
            image_result = await session.execute(
                select(Image).filter(Image.id == image_id)
            )
            image = image_result.scalars().first()
            if image is None:
                raise ImageIdInvalid(image_id)
            return image.uploader_id == user_id

    async def set_image_description(self, image_id: int, description: str) -> None:
        """Set the description for an image

        Args:
            image_id (int): The ID of the image
            description (str): The new description for the image

        Raises:
            ImageIdInvalid: If the image ID is invalid
        """
        async with self._Session() as session:
            async with session.begin():
                image_result = await session.execute(
                    select(Image).filter(Image.id == image_id)
                )
                image = image_result.scalars().first()

                if image is None:
                    raise ImageIdInvalid(image_id)

                image.description = description

    async def set_image_path(self, image_id: int, path: Union[str, Path]) -> None:
        """Set the path for an image

        Args:
            image_id (int): The ID of the image
            path (Union[str, Path]): The new path for the image

        Raises:
            ImageIdInvalid: If the image ID is invalid
        """
        async with self._Session() as session:
            async with session.begin():
                image_result = await session.execute(
                    select(Image).filter(Image.id == image_id)
                )
                image = image_result.scalars().first()

                if image is None:
                    raise ImageIdInvalid(image_id)

                image.path = str(path)

    async def get_sub_question(self, sub_question_id: int) -> Optional[SubQuestion]:
        """Get a subquestion by its ID

        Args:
            sub_question_id (int): The ID of the subquestion

        Returns:
            Optional[SubQuestion]: The subquestion object if found, otherwise None
        """
        async with self._Session() as session:
            result = await session.execute(
                select(SubQuestion).filter(SubQuestion.id == sub_question_id)
            )
            return result.scalars().first()

    async def get_question(self, question_id: int) -> Optional[Question]:
        """Get a question by its ID

        Args:
            question_id (int): The ID of the question

        Returns:
            Optional[Question]: The question object if found, otherwise None
        """
        async with self._Session() as session:
            question_result = await session.execute(
                select(Question)
                .options(joinedload(Question.sub_questions))
                # eager load sub_questions to prevent sqlalchemy.orm.exc.DetachedInstanceError
                .filter(Question.id == question_id)
            )
            question = question_result.scalars().first()
            return question

    async def get_questions_by_ids(self, question_ids: List[int]):
        """Get questions by their IDs

        Args:
            question_ids (List[int]): The IDs of the questions

        Returns:
            List[Question]: A list of question objects that match the IDs
        """
        async with self._Session() as session:
            question_result = await session.execute(
                select(Question)
                .options(joinedload(Question.sub_questions))
                # eager load sub_questions to prevent sqlalchemy.orm.exc.DetachedInstanceError
                .filter(Question.id.in_(question_ids))
            )
            return question_result.unique().scalars().all()

    async def get_questions_by_uploader_id(self, uploader_id: int) -> List[Question]:
        """Get questions by the uploader's ID

        Args:
            uploader_id (int): The ID of the uploader

        Returns:
            List[Question]: A list of question objects that match the uploader's ID
        """
        async with self._Session() as session:
            question_result = await session.execute(
                select(Question)
                .options(joinedload(Question.sub_questions))
                .filter(Question.uploader_id == uploader_id)
            )
            return question_result.unique().scalars().all()

    async def get_question_by_values(
        self,
        keyword: Optional[str] = None,
        source: Optional[str] = None,
        concept: Optional[ConceptType] = None,
        process: Optional[ProcessType] = None,
    ) -> List[Question]:
        """Get questions by their values

        Args:
            keyword (Optional[str]): The keyword to search in question name or subquestion descriptions
            source (Optional[str]): The source of the question
            concept (Optional[ConceptType]): Subquestion's concept type
            process (Optional[ProcessType]): Subquestion's process type

        Returns:
            List[Question]: A list of question objects that match the criteria
        """
        async with self._Session() as session:
            filters = []
            if keyword is not None:
                filters.append(
                    or_(
                        Question.name.icontains(keyword),
                        Question.sub_questions.any(
                            SubQuestion.description.icontains(keyword)
                        ),
                    )
                )
            if source is not None:
                filters.append(Question.source == source)
            if concept is not None:
                filters.append(
                    Question.sub_questions.any(SubQuestion.concept == concept)
                )
            if process is not None:
                filters.append(
                    Question.sub_questions.any(SubQuestion.process == process)
                )

            question_result = await session.execute(
                select(Question)
                .options(joinedload(Question.sub_questions))
                .filter(*filters)
            )
            return question_result.unique().scalars().all()

    async def get_image(self, image_id: int) -> Optional[Image]:
        """Get an image by its ID

        Args:
            image_id (int): The ID of the image

        Returns:
            Optional[Image]: The image object if found, otherwise None
        """
        async with self._Session() as session:
            result = await session.execute(select(Image).filter(Image.id == image_id))
            return result.scalars().first()

    async def approve_question(self, question_id: int) -> bool:
        """Approve a question by its ID

        Args:
            question_id (int): The ID of the question

        Raises:
            QuestionIdInvalid: If the question ID is invalid

        Returns:
            bool: True if the question was approved, False otherwise.\n
            If the question is already audited or deleted, it will return False.
        """
        async with self._Session() as session:
            async with session.begin():
                question_result = await session.execute(
                    select(Question).filter(Question.id == question_id)
                )
                question = question_result.scalars().first()

                if question is None:
                    raise QuestionIdInvalid(question_id)

                if question.is_audited:
                    return False

                question.is_audited = True
            return True

    async def delete_question(self, question_id: int) -> bool:
        """Delete a question by its ID

        Args:
            question_id (int): The ID of the question

        Raises:
            QuestionIdInvalid: If the question ID is invalid

        Returns:
            bool: True if the question was deleted, False if the question was not found.
        """
        async with self._Session() as session:
            async with session.begin():
                question_result = await session.execute(
                    select(Question).filter(Question.id == question_id)
                )
                question = question_result.scalars().first()

                if question is None:
                    raise QuestionIdInvalid(question_id)

                await session.delete(question)

            return True
