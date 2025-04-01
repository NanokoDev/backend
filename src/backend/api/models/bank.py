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
    image_id: Optional[int] = None


class Question(BaseModel):
    """API model for question"""

    id: Optional[int] = None
    source: str
    is_audited: Optional[bool] = None
    is_deleted: Optional[bool] = None
    sub_questions: List[SubQuestion]
