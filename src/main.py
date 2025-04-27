import uvicorn
from fastapi import FastAPI

import backend.config as cfg
from backend.api import router
from backend.config import Config
from backend.utils import load_config


def get_app():
    """Get the FastAPI app instance

    Returns:
        FastAPI: The FastAPI app instance
    """
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return app


def main(config: Config):
    """Run the FastAPI app

    Args:
        config (Config): The configuration object
    """
    if config.bank_db_path is not None:
        config.bank_db_path.parent.mkdir(exist_ok=True, parents=True)
    if config.image_store_path is not None:
        config.image_store_path.mkdir(exist_ok=True, parents=True)

    if config.jwt_secret is None:
        raise ValueError("JWT secret must be set in the config file")

    app = get_app()
    uvicorn.run(app, host=config.host, port=config.port)


if __name__ == "__main__":
    cfg.config = load_config()
    main(cfg.config)
