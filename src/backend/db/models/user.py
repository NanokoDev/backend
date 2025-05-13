import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Enum, DateTime
from sqlalchemy.orm import mapped_column, relationship, Mapped

from backend.db.models.base import Base
from backend.types.user import Permission, Performance
from backend.db.models.base import class_assignment_table, assignment_question_table

if TYPE_CHECKING:
    from backend.db.models.bank import SubQuestion, Question
    # avoid circular import error


class CompletedSubQuestion(Base):
    """Model for completed subquestions"""

    __tablename__ = "completed_sub_question"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    sub_question_id: Mapped[int] = mapped_column(ForeignKey("sub_question.id"))
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignment.id"))
    answer: Mapped[str] = mapped_column(String(1000))
    performance: Mapped[Performance] = mapped_column(
        Enum(Performance, create_constraint=True, native_enum=True)
    )
    feedback: Mapped[str] = mapped_column(String(1000))
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="completed_sub_questions")
    sub_question: Mapped["SubQuestion"] = relationship(
        back_populates="completed_sub_questions"
    )
    assignment: Mapped["Assignment"] = relationship(
        "Assignment",
        back_populates="completed_sub_questions",
        foreign_keys=[assignment_id],
    )

    def __repr__(self) -> str:
        return f"CompletedSubQuestion(id={self.id!r}, user_id={self.user_id!r}, sub_question_id={self.sub_question_id!r})"


class User(Base):
    """User model"""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(50))
    password_hash: Mapped[str]
    permission: Mapped[Permission] = mapped_column(
        Enum(Permission, create_constraint=True, native_enum=True)
    )
    completed_sub_questions: Mapped[List[CompletedSubQuestion]] = relationship(
        back_populates="user"
    )

    teaching_classes: Mapped[List["Class"]] = relationship(
        back_populates="teacher", foreign_keys="Class.teacher_id"
    )
    enrolled_class_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("class.id"), nullable=True
    )
    enrolled_class: Mapped[Optional["Class"]] = relationship(
        back_populates="students", foreign_keys=[enrolled_class_id]
    )

    assignments: Mapped[List["Assignment"]] = relationship(
        back_populates="teacher", foreign_keys="Assignment.teacher_id"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r}, permission={self.permission.name!r})"


class Class(Base):
    """Class model with a teacher and students"""

    __tablename__ = "class"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    enter_code: Mapped[str] = mapped_column(String(10))
    assignments: Mapped[List["Assignment"]] = relationship(
        secondary=class_assignment_table,
    )  # many to many

    teacher_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    students: Mapped[List[User]] = relationship(
        "User", back_populates="enrolled_class", foreign_keys="User.enrolled_class_id"
    )

    teacher: Mapped[User] = relationship(
        "User", back_populates="teaching_classes", foreign_keys=[teacher_id]
    )
    # Because here are two foreign keys to the same table, we need to specify which one to use for the relationship

    def __repr__(self) -> str:
        return f"Class(id={self.id!r}, teacher_id={self.teacher_id!r})"


class Assignment(Base):
    """Assignment model belonging to a teacher"""

    __tablename__ = "assignment"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(1000))
    due_date: Mapped[DateTime] = mapped_column(DateTime)

    teacher_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    teacher: Mapped[User] = relationship(
        "User", back_populates="assignments", foreign_keys=[teacher_id]
    )
    completed_sub_questions: Mapped[List[CompletedSubQuestion]] = relationship(
        "CompletedSubQuestion",
        back_populates="assignment",
        foreign_keys="CompletedSubQuestion.assignment_id",
    )

    questions: Mapped[List["Question"]] = relationship(
        secondary=assignment_question_table,
    )
