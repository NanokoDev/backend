from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from backend.types.log import LogLevel


class Config(BaseModel):
    log_level: Optional[LogLevel] = LogLevel.INFO
    host: Optional[str] = "127.0.0.1"
    port: Optional[int] = 25324
    question_db_path: Optional[Path] = Path("data/question.db")


config = Config()
# Will be changed by main.py when initialising
