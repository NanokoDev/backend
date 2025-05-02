from typing import List, Optional
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse, FileResponse
from fastapi import APIRouter, UploadFile, Body, HTTPException, Depends, status

from backend.config import config
from backend.api.models.user import User
from backend.utils import calculate_hash
from backend.types.user import Permission
from backend.types.question import ConceptType, ProcessType
from backend.db.models.bank import SubQuestion as DBSubQuestion
from backend.api.base import question_manager, get_current_user_generator
from backend.api.models.bank import Question, SubQuestion, QuestionApproveRequest
from backend.exceptions.bank import (
    ImageIdInvalid,
    QuestionIdInvalid,
    SubQuestionIdInvalid,
)


router = APIRouter(prefix="/bank", tags=["bank"])
get_current_user = get_current_user_generator(
    OAuth2PasswordBearer(tokenUrl="../user/token")
)


@router.post("/image/upload")
async def upload_image(
    file: UploadFile, current_user: User = Depends(get_current_user)
):
    """Upload an image to the server and return its hash

    Args:
        file (UploadFile): the image file to upload
        current_user (User): the user who uploaded the image

    Raises:
        HTTPException: You do not have permission to upload images
        HTTPException: unsupported content type (not JPEG or PNG)
        HTTPException: image_store_path not configured

    Returns:
        JSONResponse: the hash of the uploaded image
    """
    if current_user.permission < Permission.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to upload images!",
        )

    hash_str = await calculate_hash(file)
    if file.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content_type: {file.content_type}! Please upload a JPEG or PNG",
        )
    if config.image_store_path is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No image_store_path configured!",
        )
    image_path = (
        config.image_store_path / f"{hash_str}.{file.content_type.split('/')[-1]}"
    )
    with open(image_path, "wb") as f:
        await file.seek(0)
        f.write(await file.read())
    return JSONResponse({"hash": hash_str})


@router.post("/image/add")
async def add_image(
    description: str = Body(...),
    hash: str = Body(...),
    current_user: User = Depends(get_current_user),
):
    """Add an image to the database

    Args:
        description (str, optional): The description of the image
        hash (str, optional): The hash of the image
        current_user (User): The user who uploaded the image

    Raises:
        HTTPException: You do not have permission to add images
        HTTPException: No image_store_path configured
        HTTPException: No image with hash found
        HTTPException: Failed to add image

    Returns:
        JSONResponse: The id of the image in the database
    """
    if current_user.permission < Permission.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to add images!",
        )

    if config.image_store_path is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No image_store_path configured!",
        )

    images = list(config.image_store_path.glob(f"{hash}.*"))
    if not images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No image with hash {hash} found!",
        )
    try:
        image = await question_manager.add_image(
            description=description, path=images[0]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add image with hash {hash}: {e}",
        ) from e
    return JSONResponse({"image_id": image.id})


@router.get("/image/get", response_class=FileResponse)
async def get_image(image_id: int, current_user: User = Depends(get_current_user)):
    """Get an image from the database

    Args:
        image_id (int): The id of the image to get
        current_user (User): The user who requested the image

    Raises:
        HTTPException: No image with id found
        HTTPException: You do not have permission to get images

    Returns:
        FileResponse: The image file
    """
    if current_user.permission < Permission.STUDENT:
        # Should never happen
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to get images!",
        )

    image = await question_manager.get_image(image_id)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No image with id {image_id} found!",
        )
    return FileResponse(image.path)


@router.post("/question/add")
async def add_question(
    question: Question, current_user: User = Depends(get_current_user)
):
    """Add a question to the database

    Args:
        question (Question): The question to add
        current_user (User): The user who added the question

    Raises:
        HTTPException: You do not have permission to add questions
        HTTPException: Failed to set question

    Returns:
        JSONResponse: The id of the question in the database
    """
    if current_user.permission < Permission.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to add questions!",
        )

    sub_questions: List[DBSubQuestion] = []
    for i, sub_question in enumerate(question.sub_questions):
        sub_questions.append(
            await question_manager.add_sub_question(
                seq_number=i,
                description=sub_question.description,
                answer=sub_question.answer,
                concept=sub_question.concept,
                process=sub_question.process,
                keywords=sub_question.keywords,
            )
        )

    question_ = await question_manager.add_question(question.source)

    try:
        await question_manager.set_question(
            [sub_question.id for sub_question in sub_questions], question_.id
        )
        for i, sub_question in enumerate(sub_questions):
            if question.sub_questions[i].image_id is not None:
                await question_manager.set_sub_question_image(
                    sub_question_id=sub_question.id,
                    image_id=question.sub_questions[i].image_id,
                )
    except (SubQuestionIdInvalid, QuestionIdInvalid, ImageIdInvalid) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set question: {e}",
        ) from e

    return JSONResponse({"question_id": question_.id})


@router.get("/question/get", response_model=List[Question])
async def get_questions(
    question_id: Optional[int] = None,
    source: Optional[str] = None,
    concept: Optional[ConceptType] = None,
    process: Optional[ProcessType] = None,
    current_user: User = Depends(get_current_user),
):
    """Get questions from the database

    Args:
        question_id (Optional[int], optional): The question id of the question. Defaults to None.
        source (Optional[str], optional): The source of the question. Defaults to None.
        concept (Optional[ConceptType], optional): The concept of questions. Defaults to None.
        process (Optional[ProcessType], optional): The process of questions. Defaults to None.
        current_user (User): The user who requested the questions

    Raises:
        HTTPException: question_id is not an integer
        HTTPException: source is not a string

    Returns:
        List[Question]: The list of questions
    """
    if question_id is not None and not isinstance(question_id, int):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="question_id should be an integer!",
        )
    if source is not None and not isinstance(source, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="source should be a string!",
        )

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

        if current_user.permission >= Permission.ADMIN:
            return [question_]

        if question.is_deleted or not question.is_audited:
            return []

        return [question_]
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
        if current_user.permission >= Permission.ADMIN:
            return questions

        return [
            question
            for question in questions_
            if question.is_audited and not question.is_deleted
        ]


@router.post("/question/approve")
async def approve_question(
    question_approve_request: QuestionApproveRequest,
    current_user: User = Depends(get_current_user),
):
    """Approve a question in the database

    Args:
        question_approve_request (QuestionApproveRequest): The question approval request
        current_user (User): The user who approved the question

    Raises:
        HTTPException: You do not have permission to approve questions
        HTTPException: question_id is not an integer
        HTTPException: question_id is invalid

    Returns:
        JSONResponse: The result of the approval
    """
    if current_user.permission < Permission.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to approve questions!",
        )

    question_id = question_approve_request.question_id
    if question_id is not None and not isinstance(question_id, int):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="question_id should be an integer!",
        )

    try:
        result = await question_manager.approve_question(question_id=question_id)
    except QuestionIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with id {question_id} not found!",
        )

    if result:
        return JSONResponse({"msg": f"Approved question {question_id} successfully"})
    return JSONResponse(
        {"msg": f"Question {question_id} has already been approved or deleted"}
    )


@router.delete("/question/delete")
async def delete_question(
    question_id: int, current_user: User = Depends(get_current_user)
):
    """Delete a question in the database

    Args:
        question_id (int): The question id of the question to delete
        current_user (User): The user who deleted the question

    Raises:
        HTTPException: You do not have permission to delete questions
        HTTPException: question_id is not an integer
        HTTPException: question_id is invalid

    Returns:
        JSONResponse: The result of the deletion
    """
    if current_user.permission < Permission.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete questions!",
        )

    if question_id is not None and not isinstance(question_id, int):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="question_id should be an integer!",
        )

    try:
        result = await question_manager.delete_question(question_id=question_id)
    except QuestionIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with id {question_id} not found!",
        )

    if result:
        return JSONResponse({"msg": f"Deleted question {question_id} successfully"})
    return JSONResponse({"msg": f"Question {question_id} has already been deleted"})
