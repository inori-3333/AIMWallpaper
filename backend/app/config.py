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


class LLMProviderConfig(BaseModel):
    api_key: str = ""
    model: str = ""
    base_url: str = ""


class AIProviderConfig(BaseModel):
    default_provider: str = "openai"
    openai: LLMProviderConfig = LLMProviderConfig(model="gpt-4o")
    anthropic: LLMProviderConfig = LLMProviderConfig(model="claude-sonnet-4-20250514")
    ollama: LLMProviderConfig = LLMProviderConfig(base_url="http://localhost:11434", model="llama3")


class EmbeddingConfig(BaseModel):
    provider: str = "openai"
    openai_model: str = "text-embedding-3-small"
    local_model: str = "all-MiniLM-L6-v2"


class AppConfig(BaseModel):
    wallpaper_engine: WallpaperEngineConfig = WallpaperEngineConfig()
    storage: StorageConfig = StorageConfig()
    ai: AIProviderConfig = AIProviderConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()


def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        return AppConfig.model_validate(raw)
    return AppConfig()


config = load_config()
