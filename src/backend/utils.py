from pathlib import Path

from backend.config import Config


def load_config(config_path: Path = Path("config.json")) -> Config:
    if not config_path.exists():
        config_path.write_text(Config().model_dump_json(indent=2), encoding="utf-8")
    return Config.model_validate_json(config_path.read_text(encoding="utf-8"))
