from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Table, Column, ForeignKey


class Base(DeclarativeBase):
    pass


assignment_question_table = Table(
    "assignment_question_table",
    Base.metadata,
    Column("assignment_id", ForeignKey("assignment.id"), primary_key=True),
    Column(
        "question_id", ForeignKey("question.id", ondelete="CASCADE"), primary_key=True
    ),
)
