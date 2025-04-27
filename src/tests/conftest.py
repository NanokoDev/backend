import shutil
import asyncio
from pathlib import Path

import backend.config as cfg
from backend.utils import load_config


def pytest_configure(config):
    """Runs before tests"""
    cfg.config = load_config(Path("src/tests/test_config.json"))
    cfg.config.image_store_path.mkdir(exist_ok=True, parents=True)

    from backend.api.base import database_manager
    # Import after configuration to avoid QuestionManager use the default config

    loop = asyncio.get_event_loop()
    loop.run_until_complete(database_manager.init())


def pytest_unconfigure(config):
    """Runs after tests"""
    if cfg.config.image_store_path.exists():
        shutil.rmtree("temp_data")

    from backend.api.base import database_manager

    loop = asyncio.get_event_loop()
    loop.run_until_complete(database_manager.close())

    if cfg.config.bank_db_path is not None and cfg.config.bank_db_path.exists():
        cfg.config.bank_db_path.unlink()
