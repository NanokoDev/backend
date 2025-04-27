from typing import List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Enum
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
    performance: Mapped[Performance] = mapped_column(
        Enum(Performance, create_constraint=True, native_enum=True)
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
    name: Mapped[str] = mapped_column(String(50))
    password_hash: Mapped[str]
    password_salt: Mapped[str]
    permission: Mapped[Permission] = mapped_column(
        Enum(Permission, create_constraint=True, native_enum=True)
    )
    completed_sub_questions: Mapped[List[CompletedSubQuestion]] = relationship(
        back_populates="user"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, permission={self.permission.value!r})"
