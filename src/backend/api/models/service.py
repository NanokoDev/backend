from typing import List
from pydantic import BaseModel

from backend.api.models.user import Assignment, User
from backend.services.analyzer.models import Performances


class Overview(BaseModel):
    """Overview model for API"""

    class_name: str
    assignments: List[Assignment]
    display_name: str
    total_question_number: int
    performances: Performances


class ClassCard(BaseModel):
    """Class card model for teacher's overview"""

    class_id: int
    name: str
    student_number: int
    assignments: List[Assignment]  # with due_date, ClassAssignment from DB


class TeacherOverview(BaseModel):
    """Teacher's overview model for API"""

    classes: List[ClassCard]
    assignments: List[Assignment]  # without due_date, Assignment from DB
    students: List[User]
