from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI, UploadFile, Body
from fastapi.responses import JSONResponse, FileResponse

from backend.config import config
from backend.utils import calculate_hash
from backend.db.bank import QuestionManager
from backend.types.question import ConceptType, ProcessType
from backend.api.models.question import Question, SubQuestion
from backend.db.models.bank import SubQuestion as DBSubQuestion


question_manager = QuestionManager(
    config.bank_db_path.resolve().as_posix()
    if config.bank_db_path is not None
    else None
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await question_manager.init()
    yield
    await question_manager.close()


router = APIRouter(prefix="/bank", lifespan=lifespan)


@router.post("/image/upload")
async def upload_image(file: UploadFile):
    hash_str = await calculate_hash(file)
    if file.content_type not in {"image/jpeg", "image/png"}:
        return JSONResponse(
            {
                "msg": f"Unsupported content_type: {file.content_type}! Please upload a JPEG or PNG"
            },
            400,
        )
    if config.image_store_path is None:
        return JSONResponse({"msg": "No image_store_path configured!"}, 500)
    image_path = (
        config.image_store_path / f"{hash_str}.{file.content_type.split('/')[-1]}"
    )
    with open(image_path, "wb") as f:
        await file.seek(0)
        f.write(await file.read())
    return JSONResponse({"hash": hash_str})


@router.post("/image/add")
async def add_image(description: str = Body(...), hash: str = Body(...)):
    if config.image_store_path is None:
        return JSONResponse({"msg": "No image_store_path configured!"}, 500)

    images = list(config.image_store_path.glob(f"{hash}.*"))
    if not images:
        return JSONResponse({"msg": f"No image with hash {hash} found!"}, 500)
    image = await question_manager.add_image(description=description, path=images[0])
    return JSONResponse({"image_id": image.id})


@router.get("/image/get", response_class=FileResponse)
async def get_image(image_id: int):
    image = await question_manager.get_image(image_id)
    if image is None:
        return JSONResponse({"msg": "Image not found"}, 404)
    return FileResponse(image.path)


@router.post("/question/add")
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


@router.get("/question/get", response_model=List[Question])
async def get_questions(
    question_id: Optional[str] = None,
    source: Optional[str] = None,
    concept: Optional[ConceptType] = None,
    process: Optional[ProcessType] = None,
):
    # TODO: Authorisation
    if question_id is not None:
        question = await question_manager.get_question(question_id)
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
            source=source,
            concept=concept,
            process=process,
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


@router.delete("/question/delete")
async def delete_question(question_id: int):
    result = await question_manager.delete_question(question_id=question_id)
    if result:
        return JSONResponse({"msg": f"Deleted question {question_id} successfully"})
    return JSONResponse({"msg": f"Question {question_id} has already been deleted"})
