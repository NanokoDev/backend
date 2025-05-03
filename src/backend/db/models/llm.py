from pydantic import BaseModel

from backend.types.user import Performance


class Feedback(BaseModel):
    """Feedback model for LLM"""

    comment: str
    performance: Performance
