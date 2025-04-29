from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Table, Column, ForeignKey


class Base(DeclarativeBase):
    pass


class_assignment_table = Table(
    "class_assignment_table",
    Base.metadata,
    Column("class_id", ForeignKey("class.id"), primary_key=True),
    Column("assignment_id", ForeignKey("assignment.id"), primary_key=True),
)

assignment_question_table = Table(
    "assignment_question_table",
    Base.metadata,
    Column("assignment_id", ForeignKey("assignment.id"), primary_key=True),
    Column("question_id", ForeignKey("question.id"), primary_key=True),
)
