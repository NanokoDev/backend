import uvicorn
from fastapi import FastAPI

import backend.config as cfg
from backend.api import router
from backend.config import Config
from backend.utils import load_config


def get_app():
    app = FastAPI()
    app.include_router(router, prefix="/api")


def main(config: Config):
    if config.bank_db_path is not None:
        config.bank_db_path.parent.mkdir(exist_ok=True)
    app = get_app()
    uvicorn.run(app, host=config.host, port=config.port)


if __name__ == "__main__":
    cfg.config = load_config()
    main(cfg.config)
