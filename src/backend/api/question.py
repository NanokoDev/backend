from typing import List
from fastapi import APIRouter, FastAPI
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse, FileResponse, Response

from backend.config import config
from backend.db.question import QuestionManager
from backend.db.models.question import SubQuestion as DBSubQuestion
from backend.api.models.question import Question, SubQuestion, QuestionConstraint


question_manager = QuestionManager(config.question_db_path.resolve().as_posix())


@asynccontextmanager
async def lifespan(_: FastAPI):
    await question_manager.init()
    yield
    await question_manager.close()


router = APIRouter(prefix="/question", lifespan=lifespan)


@router.get("/image/add")
async def add_image(description: str, path: str):
    image = await question_manager.add_image(description=description, path=path)
    return JSONResponse({"image_id": image.id})


@router.get("/question/add")
async def add_question(question: Question):
    sub_questions: List[DBSubQuestion] = []
    for i, sub_question in enumerate(question.sub_questions):
        sub_questions.append(
            await question_manager.add_sub_question(
                seq_number=i,
                description=sub_question.description,
                answer=sub_question.answer,
                concept=sub_question.concept,
                process=sub_question.process,
            )
        )

    question_ = await question_manager.add_question(question.source)

    await question_manager.set_question(
        [sub_question.id for sub_question in sub_questions], question_.id
    )

    for i, sub_question in enumerate(sub_questions):
        if question.sub_questions[i].image_id is not None:
            await question_manager.set_sub_question_image(
                sub_question_id=sub_question.id,
                image_id=question.sub_questions[i].image_id,
            )

    return JSONResponse({"question_id": question_.id})


@router.get("/image/get", response_class=FileResponse)
async def get_image(image_id: int):
    image = await question_manager.get_image(image_id)
    if image is None:
        return Response("Image not found", 404)
    return FileResponse(image.path)


@router.get("/question/get", response_model=List[Question])
async def get_questions(constraint: QuestionConstraint):
    # TODO: Authorisation
    if constraint.question_id is not None:
        question = await question_manager.get_question(constraint.question_id)
        if question is None:
            return []

        question_ = Question(
            id=question.id,
            source=question.source,
            is_audited=question.is_audited,
            is_deleted=question.is_deleted,
            sub_questions=[
                SubQuestion(
                    id=sub_question.id,
                    description=sub_question.description,
                    answer=sub_question.answer,
                    concept=sub_question.concept,
                    process=sub_question.process,
                    keywords=sub_question.keywords,
                    image_id=sub_question.image_id,
                )
                for sub_question in question.sub_questions
            ],
        )

        if False:  # auth.dev
            return [question_]

        if question.is_deleted or not question.is_audited:
            return []
    else:
        questions = await question_manager.get_question_by_values(
            source=constraint.source,
            concept=constraint.concept,
            process=constraint.process,
        )
        questions_ = [
            Question(
                id=question.id,
                source=question.source,
                is_audited=question.is_audited,
                is_deleted=question.is_deleted,
                sub_questions=[
                    SubQuestion(
                        id=sub_question.id,
                        description=sub_question.description,
                        answer=sub_question.answer,
                        concept=sub_question.concept,
                        process=sub_question.process,
                        keywords=sub_question.keywords,
                        image_id=sub_question.image_id,
                    )
                    for sub_question in question.sub_questions
                ],
            )
            for question in questions
        ]
        if False:  # auth.dev
            return questions

        return [
            question
            for question in questions_
            if question.is_audited and not question.is_deleted
        ]


@router.get("/question/approve")
async def approve_question(question_id: int):
    result = await question_manager.approve_question(question_id=question_id)
    if result:
        return JSONResponse({"msg": f"Approved question {question_id} successfully"})
    return JSONResponse(
        {"msg": f"Question {question_id} has already been approved or deleted"}
    )


@router.get("/question/delete")
async def delete_question(question_id: int):
    result = await question_manager.delete_question(question_id=question_id)
    if result:
        return JSONResponse({"msg": f"Deleted question {question_id} successfully"})
    return JSONResponse({"msg": f"Question {question_id} has already been deleted"})
