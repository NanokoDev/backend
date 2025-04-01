from pathlib import Path
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import sessionmaker
from typing import Optional, Union, List
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from backend.types.question import ConceptType, ProcessType
from backend.db.models.bank import Base, Image, SubQuestion, Question
from backend.exceptions.bank import (
    ImageIdInvalid,
    QuestionIdInvalid,
    SubQuestionIdInvalid,
)


class QuestionManager:
    def __init__(self, path: Optional[str] = ":memory:"):
        self._engine = create_async_engine(f"sqlite+aiosqlite:///{path}")
        self._Session: sessionmaker[AsyncSession] = sessionmaker(
            bind=self._engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        self._Session.close_all()

    async def add_image(self, description: str, path: Union[str, Path]) -> Image:
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
    ) -> SubQuestion:
        sub_question = SubQuestion(
            seq_number=seq_number,
            description=description,
            answer=answer,
            concept=concept,
            process=process,
        )
        async with self._Session() as session:
            async with session.begin():
                session.add(sub_question)
        return sub_question

    async def add_question(self, source: str) -> Question:
        question = Question(source=source, is_audited=False, is_deleted=False)
        async with self._Session() as session:
            async with session.begin():
                session.add(question)
        return question

    async def set_sub_question_image(self, sub_question_id: int, image_id: int) -> None:
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

    async def get_question(self, question_id: int) -> Optional[Question]:
        async with self._Session() as session:
            question_result = await session.execute(
                select(Question)
                .options(joinedload(Question.sub_questions))
                # eager load sub_questions to prevent sqlalchemy.orm.exc.DetachedInstanceError
                .filter(Question.id == question_id)
            )
            question = question_result.scalars().first()
            return question

    async def get_question_by_values(
        self,
        source: Optional[str],
        concept: Optional[ConceptType],
        process: Optional[ProcessType],
    ) -> List[Question]:
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

            question_result = await session.execute(select(Question).filter(*filters))
            return question_result.scalars().all()

    async def get_image(self, image_id: int) -> Optional[Image]:
        async with self._Session() as session:
            result = await session.execute(select(Image).filter(Image.id == image_id))
            return result.scalars().first()

    async def approve_question(self, question_id: int) -> bool:
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
