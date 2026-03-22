from app.config import AppConfig, AIProviderConfig, EmbeddingConfig


class TestConfigModels:
    def test_ai_config_defaults(self):
        cfg = AppConfig()
        assert cfg.ai.default_provider == "openai"
        assert cfg.ai.openai.model == "gpt-4o"

    def test_embedding_config_defaults(self):
        cfg = AppConfig()
        assert cfg.embedding.provider == "openai"
        assert cfg.embedding.openai_model == "text-embedding-3-small"

    def test_config_from_dict(self):
        data = {
            "ai": {
                "default_provider": "anthropic",
                "anthropic": {"api_key": "sk-test", "model": "claude-sonnet-4-20250514"},
            },
            "embedding": {"provider": "local", "local_model": "all-MiniLM-L6-v2"},
        }
        cfg = AppConfig.model_validate(data)
        assert cfg.ai.default_provider == "anthropic"
        assert cfg.ai.anthropic.api_key == "sk-test"
        assert cfg.embedding.provider == "local"
