from pathlib import Path
from typing import Optional, Union
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from backend.types.question import ConceptType, ProcessType
from backend.models.question import Base, Image, Question, QuestionSet


class QuestionManager:
    def __init__(self, path: Optional[str] = ":memory:"):
        self._engine = create_async_engine(f"sqlite:///{path}")
        Base.metadata.create_all(self._engine)
        self._Session: sessionmaker[AsyncSession] = sessionmaker(
            bind=self._engine, class_=AsyncSession, expire_on_commit=False
        )

    async def add_image(self, description: str, path: Union[str, Path]) -> Image:
        image = Image(description=description, path=path)
        async with self._Session() as session:
            async with session.begin():
                await session.add(image)
                # session.begin().close will do session.commit() or rollback automatically
        return image

    async def add_question(
        self, description: str, answer: str, concept: ConceptType, process: ProcessType
    ) -> Question:
        question = Question(
            description=description, answer=answer, concept=concept, process=process
        )
        async with self._Session() as session:
            async with session.begin():
                await session.add(question)
        return question

    async def add_question_set(self, source: str) -> QuestionSet:
        question_set = QuestionSet(source=source)
        async with self._Session() as session:
            async with session.begin():
                await session.add(question_set)
        return question_set

    async def set_question_image(self, question_id: int, image_id: int) -> None:
        async with self._Session() as session:
            question_result = await session.execute(
                select(Question).filter(Question.id == question_id)
            )
            question = question_result.scalars().first()

            assert question is not None, f"Invalid question_id {question_id}"

            image_result = await session.execute(
                select(Image).filter(Image.id == image_id)
            )
            image = image_result.scalars().first()

            assert image is not None, f"Invalid image_id {image_id}"

            async with session.begin():
                question.image_id = image.id

    async def set_question_set(self, question_id: int, question_set_id: int) -> None:
        async with self._Session() as session:
            question_result = await session.execute(
                select(Question).filter(Question.id == question_id)
            )
            question = question_result.scalars().first()

            assert question is not None, f"Invalid question_id {question_id}"

            question_set_result = await session.execute(
                select(QuestionSet).filter(QuestionSet.id == question_set_id)
            )
            question_set = question_set_result.scalars().first()

            assert question_set is not None, (
                f"Invalid question_set_id {question_set_id}"
            )

            async with session.begin():
                question.question_set_id = question_set.id

    async def get_question(self, question_id: int) -> Optional[Question]:
        async with self._Session() as session:
            question_result = await session.execute(
                select(Question).filter(Question.id == question_id)
            )
            return question_result.scalars().first()

    async def get_question_set(self, question_set_id: int) -> Optional[QuestionSet]:
        async with self._Session() as session:
            question_set_result = await session.execute(
                select(QuestionSet).filter(QuestionSet.id == question_set_id)
            )
            return question_set_result.scalars().first()
