import shutil
import asyncio
from pathlib import Path

import backend.config as cfg
from backend.utils import load_config


def pytest_configure(config):
    cfg.config = load_config(Path("src/tests/test_config.json"))
    cfg.config.image_store_path.mkdir(exist_ok=True, parents=True)

    from backend.api.bank import question_manager

    loop = asyncio.get_event_loop()
    loop.run_until_complete(question_manager.init())


def pytest_unconfigure(config):
    if cfg.config.image_store_path.exists():
        shutil.rmtree("temp_data")

    from backend.api.bank import question_manager

    loop = asyncio.get_event_loop()
    loop.run_until_complete(question_manager.close())

    if cfg.config.bank_db_path is not None and cfg.config.bank_db_path.exists():
        cfg.config.bank_db_path.unlink()
