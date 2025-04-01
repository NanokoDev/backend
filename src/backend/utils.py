import hashlib
from pathlib import Path
from fastapi import UploadFile

from backend.config import Config


def load_config(config_path: Path = Path("config.json")) -> Config:
    """Load the configuration from a JSON file.

    Args:
        config_path (Path, optional): The path to the config JSON. Defaults to Path("config.json").

    Returns:
        Config: The loaded configuration.
    """
    if not config_path.exists():
        config_path.write_text(Config().model_dump_json(indent=2), encoding="utf-8")
    return Config.model_validate_json(config_path.read_text(encoding="utf-8"))


async def calculate_hash(file: UploadFile, hash_type: str = "md5") -> str:
    """Calculate the hash of a file

    Args:
        file (UploadFile): The file needs to calculate hash
        hash_type (str, optional): The type of hash. Defaults to "md5".

    Returns:
        str: The hash of the file
    """
    hash_func = hashlib.new(hash_type)
    chunk = await file.read(4096)
    while chunk != b"":
        hash_func.update(chunk)
        chunk = await file.read(4096)
    # avoid high memory by reading in blocks
    return hash_func.hexdigest()
