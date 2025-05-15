from pydantic import BaseModel
from typing import List, Optional

from backend.types.question import ConceptType, ProcessType


class SubQuestion(BaseModel):
    """API model for subquestion"""

    id: Optional[int] = None
    description: str
    answer: str
    concept: ConceptType
    process: ProcessType
    keywords: Optional[List[str]] = None
    options: Optional[List[str]] = None
    image_id: Optional[int] = None


class Question(BaseModel):
    """API model for question"""

    id: Optional[int] = None
    source: str
    is_audited: Optional[bool] = None
    is_deleted: Optional[bool] = None
    sub_questions: List[SubQuestion]


class QuestionApproveRequest(BaseModel):
    """API model for question approval request"""

    question_id: int


class ImageAddRequest(BaseModel):
    """API model for image addition request"""

    description: str
    hash: str


class ImageDescriptionRequest(BaseModel):
    """API model for image description request"""

    image_id: int
    description: str


class ImageHashRequest(BaseModel):
    """API model for image hash request"""

    image_id: int
    hash: str


class SubQuestionDescriptionRequest(BaseModel):
    """API model for sub-question description request"""

    sub_question_id: int
    description: str


class SubQuestionOptionsRequest(BaseModel):
    """API model for sub-question options request"""

    sub_question_id: int
    options: List[str]


class SubQuestionAnswerRequest(BaseModel):
    """API model for sub-question answer request"""

    sub_question_id: int
    answer: str


class SubQuestionConceptRequest(BaseModel):
    """API model for sub-question concept request"""

    sub_question_id: int
    concept: ConceptType


class SubQuestionProcessRequest(BaseModel):
    """API model for sub-question process request"""

    sub_question_id: int
    process: ProcessType


class SubQuestionKeywordsRequest(BaseModel):
    """API model for sub-question keywords request"""

    sub_question_id: int
    keywords: List[str]


class SubQuestionImageRequest(BaseModel):
    """API model for sub-question image request"""

    sub_question_id: int
    image_id: int
