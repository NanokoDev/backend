from pydantic import BaseModel
from typing import Literal, List


class LLMMessage(BaseModel):
    """LLM message model for LLM"""

    role: Literal["user", "assistant"]
    content: str


class LLMHintRequest(BaseModel):
    """LLM hint request model for LLM"""

    sub_question_id: int
    question: str
    context: List[LLMMessage]
