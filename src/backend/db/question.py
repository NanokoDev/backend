from pathlib import Path
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from typing import Optional, Union, List
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from backend.types.question import ConceptType, ProcessType
from backend.db.models.question import Base, Image, SubQuestion, Question


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

    async def add_sub_question(
        self, description: str, answer: str, concept: ConceptType, process: ProcessType
    ) -> Question:
        sub_question = SubQuestion(
            description=description, answer=answer, concept=concept, process=process
        )
        async with self._Session() as session:
            async with session.begin():
                await session.add(sub_question)
        return sub_question

    async def add_question(self, source: str) -> Question:
        question = Question(source=source)
        async with self._Session() as session:
            async with session.begin():
                await session.add(question)
        return question

    async def set_sub_question_image(self, question_id: int, image_id: int) -> None:
        async with self._Session() as session:
            sub_question_result = await session.execute(
                select(SubQuestion).filter(SubQuestion.id == question_id)
            )
            sub_question = sub_question_result.scalars().first()

            assert sub_question is not None, f"Invalid question_id {question_id}"

            image_result = await session.execute(
                select(Image).filter(Image.id == image_id)
            )
            image = image_result.scalars().first()

            assert image is not None, f"Invalid image_id {image_id}"

            async with session.begin():
                sub_question.image_id = image.id

    async def set_question(self, sub_question_ids: List[int], question_id: int) -> None:
        async with self._Session() as session:
            sub_question_result = await session.execute(
                select(SubQuestion).filter(SubQuestion.id.in_(sub_question_ids))
            )
            sub_questions = sub_question_result.scalars().all()

            assert len(sub_questions) == len(sub_question_ids), "Invalid question_id(s)"

            question_result = await session.execute(
                select(Question).filter(Question.id == question_id)
            )
            question = question_result.scalars().first()

            assert question is not None, f"Invalid question_id {question_id}"

            async with session.begin():
                for sub_question in sub_questions:
                    sub_question.question_id = question.id

    async def get_question(self, question_id: int) -> Optional[Question]:
        async with self._Session() as session:
            question_result = await session.execute(
                select(Question).filter(Question.id == question_id)
            )
            return question_result.scalars().first()
