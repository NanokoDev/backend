import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Enum, DateTime
from sqlalchemy.orm import mapped_column, relationship, Mapped

from backend.db.models.base import Base
from backend.types.user import Permission, Performance

if TYPE_CHECKING:
    from backend.db.models.bank import SubQuestion
    # avoid circular import error


class CompletedSubQuestion(Base):
    """Model for completed subquestions"""

    __tablename__ = "completed_sub_question"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    sub_question_id: Mapped[int] = mapped_column(ForeignKey("sub_question.id"))
    answer: Mapped[str] = mapped_column(String(1000))
    performance: Mapped[Performance] = mapped_column(
        Enum(Performance, create_constraint=True, native_enum=True)
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, default=datetime.datetime.now(datetime.timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="completed_sub_questions")
    sub_question: Mapped["SubQuestion"] = relationship(
        back_populates="completed_sub_questions"
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

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r}, permission={self.permission.value!r})"
