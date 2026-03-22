import time
from litellm import completion as litellm_completion
from app.config import AppConfig


class AIEngine:
    def __init__(self, provider: str, model: str, api_key: str = "", base_url: str = "", max_retries: int = 3):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.max_retries = max_retries

    def _model_string(self) -> str:
        if self.provider == "ollama":
            return f"ollama/{self.model}"
        return self.model

    def chat(self, system_prompt: str, messages: list[dict], temperature: float = 0.7) -> str:
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        kwargs = {"model": self._model_string(), "messages": full_messages, "temperature": temperature}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["api_base"] = self.base_url

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = litellm_completion(**kwargs)
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(1 * (attempt + 1))
        raise last_error

    @classmethod
    def from_config(cls, cfg: AppConfig) -> "AIEngine":
        provider = cfg.ai.default_provider
        provider_cfg = getattr(cfg.ai, provider)
        return cls(
            provider=provider,
            model=provider_cfg.model,
            api_key=provider_cfg.api_key,
            base_url=provider_cfg.base_url,
        )
