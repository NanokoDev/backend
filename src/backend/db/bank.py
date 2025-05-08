from pathlib import Path
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import Optional, Union, List

from backend.db.base import DatabaseManager
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

    async def add_image(self, description: str, path: Union[str, Path]) -> Image:
        """Add an image to the database

        Args:
            description (str): The description of the image
            path (Union[str, Path]): The path to the image file

        Returns:
            Image: The image object that was added to the database
        """
        image = Image(description=description, path=str(path))
        async with self._Session() as session:
            async with session.begin():
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

    async def add_question(self, source: str) -> Question:
        """Add a question to the database

        Args:
            source (str): The source of the question

        Returns:
            Question: The question object that was added to the database
        """
        question = Question(source=source, is_audited=False, is_deleted=False)
        async with self._Session() as session:
            async with session.begin():
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
                select(Question).filter(Question.id.in_(question_ids))
            )
            return question_result.scalars().all()

    async def get_question_by_values(
        self,
        source: Optional[str],
        concept: Optional[ConceptType],
        process: Optional[ProcessType],
    ) -> List[Question]:
        """Get questions by their values

        Args:
            source (Optional[str]): The source of the question
            concept (Optional[ConceptType]): Subquestion's concept type
            process (Optional[ProcessType]): Subquestion's process type

        Returns:
            List[Question]: A list of question objects that match the criteria
        """
        async with self._Session() as session:
            filters = []
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

                if question.is_audited or question.is_deleted:
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
            bool: True if the question was deleted, False otherwise.\n
            If the question is already deleted, it will return False.
        """
        async with self._Session() as session:
            async with session.begin():
                question_result = await session.execute(
                    select(Question).filter(Question.id == question_id)
                )
                question = question_result.scalars().first()

                if question is None:
                    raise QuestionIdInvalid(question_id)

                if question.is_deleted:
                    return False

                question.is_deleted = True

            return True
