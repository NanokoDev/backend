from pydantic import BaseModel
from typing import List, Optional

from backend.types.question import ConceptType, ProcessType


class SubQuestion(BaseModel):
    id: Optional[int]
    description: str
    answer: str
    concept: ConceptType
    process: ProcessType
    keywords: Optional[List[str]]
    image_id: Optional[int]


class Question(BaseModel):
    id: Optional[int]
    source: str
    is_audited: bool
    is_deleted: bool
    sub_questions: List[SubQuestion]


class QuestionConstraint(BaseModel):
    question_id: Optional[str]
    source: Optional[str]
    concept: Optional[ConceptType]
    process: Optional[ProcessType]
