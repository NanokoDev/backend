from typing import List, Optional
from sqlalchemy import String, Boolean, Integer, CheckConstraint, ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped, DeclarativeBase

from backend.types.question import ConceptType, ProcessType


class Base(DeclarativeBase):
    pass


class Image(Base):
    __tablename__ = "image"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(50))
    path: Mapped[str] = mapped_column(String(255))

    questions: Mapped[List["Question"]] = relationship(back_populates="image")

    def __repr__(self) -> str:
        return f"Image(id={self.id!r}, description={self.description!r}, path={self.path!r})"


class Question(Base):
    __tablename__ = "question"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]
    answer: Mapped[str]
    concept: Mapped[ConceptType] = mapped_column(Integer)
    process: Mapped[ProcessType] = mapped_column(Integer)
    keywords: Mapped[Optional[str]]
    # sperated with "," e.g. "225 million years ago,one kilogram,25 grams"

    image_id = mapped_column(ForeignKey("image.id"), nullable=True)
    question_set_id = mapped_column(ForeignKey("question_set.id"))

    image: Mapped[Optional["Image"]] = relationship(back_populates="questions")
    question_set = Mapped["QuestionSet"] = relationship(back_populates="questions")

    __table_args__ = (
        CheckConstraint(
            f"concept IN ({','.join(str(e.value) for e in ConceptType)})",
            name="check_concept",
        ),
        CheckConstraint(
            f"process IN ({','.join(str(e.value) for e in ProcessType)})",
            name="check_process",
        ),
    )

    def __repr__(self) -> str:
        return f"Question(id={self.id!r}, concept={self.concept!r}, process={self.process!r})"


class QuestionSet(Base):
    __tablename__ = "question_set"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str]
    is_audited: Mapped[bool] = mapped_column(Boolean, default=Boolean(False))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=Boolean(False))

    questions: Mapped[List["Question"]] = relationship(back_populates="question_set")

    def __repr__(self):
        return f"Question(id={self.id!r}, questions={self.questions!r})"
