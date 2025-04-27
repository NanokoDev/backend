from backend.config import config
from backend.db.base import DatabaseManager


database_manager = DatabaseManager(
    config.bank_db_path.resolve().as_posix()
    if config.bank_db_path is not None
    else ":memory:"
)
