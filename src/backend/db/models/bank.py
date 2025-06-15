from typing import List, Optional
from sqlalchemy import String, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import mapped_column, relationship, Mapped

from backend.db.models.base import Base
from backend.types.question import ConceptType, ProcessType
from backend.db.models.user import CompletedSubQuestion, User


class Image(Base):
    """Image model for the question bank"""

    __tablename__ = "image"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(50))
    path: Mapped[str] = mapped_column(String(255))
    uploader_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    uploader: Mapped[User] = relationship(
        "User", back_populates="images", foreign_keys=[uploader_id]
    )

    sub_questions: Mapped[List["SubQuestion"]] = relationship(back_populates="image")

    def __repr__(self) -> str:
        return f"Image(id={self.id!r}, description={self.description!r}, path={self.path!r})"


class SubQuestion(Base):
    """SubQuestion model for the question bank"""

    __tablename__ = "sub_question"

    id: Mapped[int] = mapped_column(primary_key=True)
    seq_number: Mapped[int]
    # be used to sort subquestions
    description: Mapped[str]
    options: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    # ["option1", "option2", ...]
    answer: Mapped[str]
    concept: Mapped[ConceptType] = mapped_column(
        Enum(ConceptType, create_constraint=True, native_enum=True)
    )
    process: Mapped[ProcessType] = mapped_column(
        Enum(ProcessType, create_constraint=True, native_enum=True)
    )
    keywords: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    # ["keyword1", "keyword2", ...]

    image_id = mapped_column(ForeignKey("image.id"), nullable=True)
    question_id = mapped_column(ForeignKey("question.id"))

    image: Mapped[Optional["Image"]] = relationship(back_populates="sub_questions")
    question: Mapped["Question"] = relationship(back_populates="sub_questions")

    completed_sub_questions: Mapped[List[CompletedSubQuestion]] = relationship(
        back_populates="sub_question"
    )

    def __repr__(self) -> str:
        return f"SubQuestion(id={self.id!r}, concept={self.concept!r}, process={self.process!r})"


class Question(Base):
    """Question model for the question bank"""

    __tablename__ = "question"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    source: Mapped[str] = mapped_column(String(100))
    uploader_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    is_audited: Mapped[bool] = mapped_column(Boolean, default=Boolean(False))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=Boolean(False))

    uploader: Mapped[User] = relationship(
        "User", back_populates="questions", foreign_keys=[uploader_id]
    )
    sub_questions: Mapped[List[SubQuestion]] = relationship(back_populates="question")

    def __repr__(self):
        return f"Question(id={self.id!r}, name={self.name!r}, source={self.source!r}, is_audited={self.is_audited!r}, is_deleted={self.is_deleted!r})"
