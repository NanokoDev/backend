import uvicorn
from pathlib import Path
from fastapi import FastAPI

import backend.config as cfg
from backend.api import router
from backend.config import Config


def load_config() -> Config:
    config_path = Path("config.json")
    if not config_path.exists():
        config_path.write_text(Config().model_dump_json(indent=2), encoding="utf-8")
    return Config.model_validate_json(config_path.read_text(encoding="utf-8"))


def main(config: Config):
    config.bank_db_path.parent.mkdir(exist_ok=True)

    app = FastAPI()
    app.include_router(router, prefix="/api")

    uvicorn.run(app, host=config.host, port=config.port)


if __name__ == "__main__":
    cfg.config = load_config()
    main(cfg.config)
