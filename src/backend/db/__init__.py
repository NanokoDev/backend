from openai import AsyncOpenAI

from backend.config import config
from backend.db.llm import LLMManager
from backend.db.user import UserManager
from backend.db.base import DatabaseManager
from backend.db.bank import QuestionManager
from backend.services.analyzer import Analyzer


database_manager = DatabaseManager(
    config.bank_db_path.resolve().as_posix()
    if config.bank_db_path is not None
    else ":memory:"
)
llm_manager = LLMManager(
    database_manager=database_manager,
    client=AsyncOpenAI(
        api_key=config.llm_api_key,
        base_url=config.llm_api_base_url,
    ),
    model=config.llm_model,
)
user_manager = UserManager(database_manager=database_manager)
question_manager = QuestionManager(database_manager=database_manager)
analyzer = Analyzer(user_manager=user_manager)
