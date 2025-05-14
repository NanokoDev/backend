from typing import List, Optional
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse, FileResponse
from fastapi import APIRouter, UploadFile, HTTPException, Depends, status

from backend.config import config
from backend.db import question_manager
from backend.api.models.user import User
from backend.utils import calculate_hash
from backend.types.user import Permission
from backend.api.base import get_current_user_generator
from backend.types.question import ConceptType, ProcessType
from backend.db.models.bank import SubQuestion as DBSubQuestion
from backend.api.models.bank import (
    Question,
    SubQuestion,
    ImageAddRequest,
    ImageHashRequest,
    QuestionApproveRequest,
    ImageDescriptionRequest,
    SubQuestionImageRequest,
    SubQuestionAnswerRequest,
    SubQuestionConceptRequest,
    SubQuestionOptionsRequest,
    SubQuestionProcessRequest,
    SubQuestionKeywordsRequest,
    SubQuestionDescriptionRequest,
)
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
    request: ImageAddRequest,
    current_user: User = Depends(get_current_user),
):
    """Add an image to the database

    Args:
        request (ImageAddRequest): The request containing description and hash
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

    images = list(config.image_store_path.glob(f"{request.hash}.*"))
    if not images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No image with hash {request.hash} found!",
        )
    try:
        image = await question_manager.add_image(
            description=request.description, path=images[0]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add image with hash {request.hash}: {e}",
        ) from e
    return JSONResponse({"image_id": image.id})


@router.post("/image/set/description")
async def set_image_description(
    request: ImageDescriptionRequest,
    current_user: User = Depends(get_current_user),
):
    """Set the description of an image

    Args:
        request (ImageDescriptionRequest): The request containing image_id and description
        current_user (User): The user who set the description

    Raises:
        HTTPException: You do not have permission to set descriptions
        HTTPException: No image with id found
        HTTPException: Failed to set description

    Returns:
        JSONResponse: The result of the operation
    """
    if current_user.permission < Permission.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to set descriptions!",
        )

    try:
        await question_manager.set_image_description(
            image_id=request.image_id, description=request.description
        )
    except ImageIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No image with id {request.image_id} found!",
        )

    return JSONResponse({"msg": f"Set description of image {request.image_id}"})


@router.post("/image/set/hash")
async def set_image_hash(
    request: ImageHashRequest,
    current_user: User = Depends(get_current_user),
):
    """Set the hash of an image

    Args:
        request (ImageHashRequest): The request containing image_id and hash
        current_user (User): The user who set the hash

    Raises:
        HTTPException: You do not have permission to set hashes
        HTTPException: No image with id found
        HTTPException: No image with hash found

    Returns:
        JSONResponse: The result of the operation
    """
    if current_user.permission < Permission.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to set hashes!",
        )

    image_paths = list(config.image_store_path.glob(f"{request.hash}.*"))
    if not image_paths:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No image with hash {request.hash} found!",
        )

    image_path = image_paths[0]

    try:
        await question_manager.set_image_path(
            image_id=request.image_id, path=image_path
        )
    except ImageIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No image with id {request.image_id} found!",
        )

    return JSONResponse({"msg": f"Set hash of image {request.image_id}"})


@router.get("/image/get/description")
async def get_image_description(
    image_id: int, current_user: User = Depends(get_current_user)
):
    """Get the description of an image

    Args:
        image_id (int): The id of the image to get
        current_user (User): The user who requested the image

    Raises:
        HTTPException: No image with id found
        HTTPException: You do not have permission to get images

    Returns:
        JSONResponse: The description of the image
    """
    if current_user.permission < Permission.STUDENT:
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
    return JSONResponse({"description": image.description})


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
                options=sub_question.options,
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


@router.post("/sub-question/set/description")
async def set_sub_question_description(
    request: SubQuestionDescriptionRequest,
    current_user: User = Depends(get_current_user),
):
    """Set the description of a sub-question

    Args:
        request (SubQuestionDescriptionRequest): The request containing sub_question_id and description
        current_user (User): The user who set the description

    Raises:
        HTTPException: You do not have permission to set descriptions
        HTTPException: No sub-question with id found
        HTTPException: Failed to set description

    Returns:
        JSONResponse: The result of the operation
    """
    if current_user.permission < Permission.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to set descriptions!",
        )

    try:
        await question_manager.set_sub_question_description(
            sub_question_id=request.sub_question_id, description=request.description
        )
    except SubQuestionIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sub-question with id {request.sub_question_id} found!",
        )

    return JSONResponse(
        {"msg": f"Set description of sub-question {request.sub_question_id}"}
    )


@router.post("/sub-question/set/options")
async def set_sub_question_options(
    request: SubQuestionOptionsRequest,
    current_user: User = Depends(get_current_user),
):
    """Set the options of a sub-question

    Args:
        request (SubQuestionOptionsRequest): The request containing sub_question_id and options
        current_user (User): The user who set the options

    Raises:
        HTTPException: You do not have permission to set options
        HTTPException: No sub-question with id found
        HTTPException: Failed to set options

    Returns:
        JSONResponse: The result of the operation
    """
    if current_user.permission < Permission.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to set options!",
        )

    try:
        await question_manager.set_sub_question_options(
            sub_question_id=request.sub_question_id, options=request.options
        )
    except SubQuestionIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sub-question with id {request.sub_question_id} found!",
        )

    return JSONResponse(
        {"msg": f"Set options of sub-question {request.sub_question_id}"}
    )


@router.post("/sub-question/set/answer")
async def set_sub_question_answer(
    request: SubQuestionAnswerRequest,
    current_user: User = Depends(get_current_user),
):
    """Set the answer of a sub-question

    Args:
        request (SubQuestionAnswerRequest): The request containing sub_question_id and answer
        current_user (User): The user who set the answer

    Raises:
        HTTPException: You do not have permission to set answers
        HTTPException: No sub-question with id found
        HTTPException: Failed to set answer

    Returns:
        JSONResponse: The result of the operation
    """
    if current_user.permission < Permission.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to set answers!",
        )

    try:
        await question_manager.set_sub_question_answer(
            sub_question_id=request.sub_question_id, answer=request.answer
        )
    except SubQuestionIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sub-question with id {request.sub_question_id} found!",
        )

    return JSONResponse(
        {"msg": f"Set answer of sub-question {request.sub_question_id}"}
    )


@router.post("/sub-question/set/concept")
async def set_sub_question_concept(
    request: SubQuestionConceptRequest,
    current_user: User = Depends(get_current_user),
):
    """Set the concept of a sub-question

    Args:
        request (SubQuestionConceptRequest): The request containing sub_question_id and concept
        current_user (User): The user who set the concept

    Raises:
        HTTPException: You do not have permission to set concepts
        HTTPException: No sub-question with id found
        HTTPException: Failed to set concept

    Returns:
        JSONResponse: The result of the operation
    """
    if current_user.permission < Permission.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to set concepts!",
        )

    try:
        await question_manager.set_sub_question_concept(
            sub_question_id=request.sub_question_id, concept=request.concept
        )
    except SubQuestionIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sub-question with id {request.sub_question_id} found!",
        )

    return JSONResponse(
        {"msg": f"Set concept of sub-question {request.sub_question_id}"}
    )


@router.post("/sub-question/set/process")
async def set_sub_question_process(
    request: SubQuestionProcessRequest,
    current_user: User = Depends(get_current_user),
):
    """Set the process of a sub-question

    Args:
        request (SubQuestionProcessRequest): The request containing sub_question_id and process
        current_user (User): The user who set the process

    Raises:
        HTTPException: You do not have permission to set processes
        HTTPException: No sub-question with id found
        HTTPException: Failed to set process

    Returns:
        JSONResponse: The result of the operation
    """
    if current_user.permission < Permission.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to set processes!",
        )

    try:
        await question_manager.set_sub_question_process(
            sub_question_id=request.sub_question_id, process=request.process
        )
    except SubQuestionIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sub-question with id {request.sub_question_id} found!",
        )

    return JSONResponse(
        {"msg": f"Set process of sub-question {request.sub_question_id}"}
    )


@router.post("/sub-question/set/keywords")
async def set_sub_question_keywords(
    request: SubQuestionKeywordsRequest,
    current_user: User = Depends(get_current_user),
):
    """Set the keywords of a sub-question

    Args:
        request (SubQuestionKeywordsRequest): The request containing sub_question_id and keywords
        current_user (User): The user who set the keywords

    Raises:
        HTTPException: You do not have permission to set keywords
        HTTPException: No sub-question with id found
        HTTPException: Failed to set keywords

    Returns:
        JSONResponse: The result of the operation
    """
    if current_user.permission < Permission.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to set keywords!",
        )

    try:
        await question_manager.set_sub_question_keywords(
            sub_question_id=request.sub_question_id, keywords=request.keywords
        )
    except SubQuestionIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sub-question with id {request.sub_question_id} found!",
        )

    return JSONResponse(
        {"msg": f"Set keywords of sub-question {request.sub_question_id}"}
    )


@router.post("/sub-question/set/image")
async def set_sub_question_image(
    request: SubQuestionImageRequest,
    current_user: User = Depends(get_current_user),
):
    """Set the image of a sub-question

    Args:
        request (SubQuestionImageRequest): The request containing sub_question_id and image_id
        current_user (User): The user who set the image

    Raises:
        HTTPException: You do not have permission to set images
        HTTPException: No sub-question with id found
        HTTPException: No image with id found
        HTTPException: Failed to set image

    Returns:
        JSONResponse: The result of the operation
    """
    if current_user.permission < Permission.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to set images!",
        )

    try:
        await question_manager.set_sub_question_image(
            sub_question_id=request.sub_question_id, image_id=request.image_id
        )
    except SubQuestionIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sub-question with id {request.sub_question_id} found!",
        )
    except ImageIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No image with id {request.image_id} found!",
        )

    return JSONResponse({"msg": f"Set image of sub-question {request.sub_question_id}"})


@router.delete("/sub-question/delete/image")
async def delete_sub_question_image(
    sub_question_id: int, current_user: User = Depends(get_current_user)
):
    """Delete the image of a sub-question

    Args:
        sub_question_id (int): The id of the sub-question
        current_user (User): The user who deleted the image

    Raises:
        HTTPException: You do not have permission to delete images
        HTTPException: No sub-question with id found

    Returns:
        JSONResponse: The result of the operation
    """
    if current_user.permission < Permission.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete images!",
        )

    try:
        await question_manager.delete_sub_question_image(
            sub_question_id=sub_question_id
        )
    except SubQuestionIdInvalid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sub-question with id {sub_question_id} found!",
        )

    return JSONResponse({"msg": f"Deleted image of sub-question {sub_question_id}"})


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
