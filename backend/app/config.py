from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import yaml

CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"


class WallpaperEngineConfig(BaseModel):
    path: str = ""
    exe: str = "wallpaper32.exe"


class StorageConfig(BaseModel):
    data_dir: str = "./data"
    max_upload_size_mb: int = 500
    preview_timeout_seconds: int = 10


class AppConfig(BaseModel):
    wallpaper_engine: WallpaperEngineConfig = WallpaperEngineConfig()
    storage: StorageConfig = StorageConfig()


def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        return AppConfig.model_validate(raw)
    return AppConfig()


config = load_config()
