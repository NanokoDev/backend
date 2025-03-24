from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from backend.types.log import LogLevel


@dataclass
class Config:
    log_level: Optional[LogLevel] = LogLevel.INFO
    question_db_path: Optional[Path] = Path("data/question.db")


config = Config()
# Will be changed by main.py when initialising
