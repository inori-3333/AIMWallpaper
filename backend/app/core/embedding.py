from litellm import embedding as litellm_embedding
from app.config import AppConfig


class EmbeddingService:
    def __init__(self, provider: str, model: str, api_key: str = ""):
        self.provider = provider
        self.model = model
        self.api_key = api_key

    def _model_string(self) -> str:
        return self.model

    def embed(self, text: str) -> list[float]:
        kwargs = {"model": self._model_string(), "input": [text]}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        response = litellm_embedding(**kwargs)
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        kwargs = {"model": self._model_string(), "input": texts}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        response = litellm_embedding(**kwargs)
        return [item.embedding for item in response.data]

    @classmethod
    def from_config(cls, cfg: AppConfig) -> "EmbeddingService":
        provider = cfg.embedding.provider
        if provider == "openai":
            model = cfg.embedding.openai_model
        else:
            model = cfg.embedding.local_model
        api_key = cfg.ai.openai.api_key if provider == "openai" else ""
        return cls(provider=provider, model=model, api_key=api_key)
