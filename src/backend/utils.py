import hashlib
from pathlib import Path
from fastapi import UploadFile

from backend.config import Config


def load_config(config_path: Path = Path("config.json")) -> Config:
    if not config_path.exists():
        config_path.write_text(Config().model_dump_json(indent=2), encoding="utf-8")
    return Config.model_validate_json(config_path.read_text(encoding="utf-8"))


async def calculate_hash(file: UploadFile, hash_type: str = "md5") -> str:
    hash_func = hashlib.new(hash_type)
    chunk = await file.read(4096)
    while chunk != b"":
        hash_func.update(chunk)
        chunk = await file.read(4096)
    # avoid high memory by reading in blocks
    return hash_func.hexdigest()
