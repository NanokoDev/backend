from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from backend.types.log import LogLevel


class Config(BaseModel):
    """The configuration for the backend"""

    log_level: Optional[LogLevel] = LogLevel.INFO
    host: Optional[str] = "127.0.0.1"
    port: Optional[int] = 25324

    bank_db_path: Optional[Path] = Path("data/bank.db")
    image_store_path: Optional[Path] = Path("data/images")

    jwt_secret: Optional[str] = None

    admin_username: Optional[str] = "admin"
    admin_password: Optional[str] = "password"
    admin_email: Optional[str] = "admin@example.com"
    admin_display_name: Optional[str] = "Admin"

    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_api_base_url: Optional[str] = None


config = Config()
# Will be changed by main.py when initialising
