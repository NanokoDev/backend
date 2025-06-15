from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

from backend.types.user import Permission, Performance
from backend.services.analyzer.models import Performances
from backend.api.models.bank import Question, SubQuestion


class Token(BaseModel):
    """Token model for authentication"""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model"""

    username: Optional[str] = None


class User(BaseModel):
    """User model for API"""

    id: int
    name: str
    display_name: str
    email: str
    permission: Permission


class Class(BaseModel):
    """Class model for API"""

    id: int
    name: str
    enter_code: str
    teacher_id: int


class FeedBack(BaseModel):
    """Feedback model for API"""

    comment: str
    performance: Performance


class Assignment(BaseModel):
    """Assignment model for API"""

    id: int
    name: str
    description: str
    teacher_id: int
    question_ids: List[int]
    due_date: Optional[datetime] = None


class ClassData(BaseModel):
    """Class data model for API"""

    class_name: str
    teacher_name: str
    to_do_assignments: List[Assignment]
    done_assignments: List[Assignment]


class TeacherClassData(BaseModel):
    """Teacher class data model for API"""

    class_id: int
    name: str
    enter_code: str
    students: List[User]
    assignments: List[Assignment]
    performances: Performances


class StudentPerformance(BaseModel):
    """Student performance model for API"""

    user: User
    answer: Optional[str] = None
    performance: Optional[Performance] = None
    feedback: Optional[str] = None
    date: Optional[datetime] = None
    # If none, then the student did not submit


class ReviewSubQuestion(SubQuestion):
    """Review sub-question model for API"""

    student_performances: List[StudentPerformance]


class ReviewQuestion(Question):
    """Review question model for API"""

    sub_questions: List[ReviewSubQuestion]


class AssignmentReviewData(BaseModel):
    """Assignment review data model for API"""

    title: str
    questions: List[ReviewQuestion]


class UserRegisterRequest(BaseModel):
    """User registration request model"""

    username: str
    email: str
    display_name: str
    password: str
    permission: Permission


class SubmitAnswerRequest(BaseModel):
    """Submit answer request model"""

    sub_question_id: int
    assignment_id: int
    answer: str


class ResetPasswordRequest(BaseModel):
    """Reset password request model"""

    old_password: str
    new_password: str


class CreateClassRequest(BaseModel):
    """Create class request model"""

    class_name: str
    enter_code: str


class JoinClassRequest(BaseModel):
    """Join class request model"""

    class_name: str
    enter_code: str


class KickStudentRequest(BaseModel):
    """Kick student request model"""

    student_id: int


class CreateAssignmentRequest(BaseModel):
    """Create assignment request model"""

    assignment_name: str
    description: str
    question_ids: List[int]


class AssignAssignmentRequest(BaseModel):
    """Assign assignment request model"""

    assignment_id: int
    class_id: int
    due_date: datetime
