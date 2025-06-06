from typing import List
from pydantic import BaseModel

from backend.api.models.user import Assignment
from backend.services.analyzer.models import Performances


class Overview(BaseModel):
    """Overview model for API"""

    class_name: str
    assignments: List[Assignment]
    display_name: str
    total_question_number: int
    performances: Performances
