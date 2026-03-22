import pytest
from unittest.mock import patch, MagicMock
from app.core.embedding import EmbeddingService


class TestEmbeddingService:
    @patch("app.core.embedding.litellm_embedding")
    def test_embed_text(self, mock_embed):
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_embed.return_value = mock_response
        svc = EmbeddingService(provider="openai", model="text-embedding-3-small", api_key="sk-test")
        result = svc.embed("rain effect")
        assert result == [0.1, 0.2, 0.3]
        mock_embed.assert_called_once()

    @patch("app.core.embedding.litellm_embedding")
    def test_embed_batch(self, mock_embed):
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2]), MagicMock(embedding=[0.3, 0.4])]
        mock_embed.return_value = mock_response
        svc = EmbeddingService(provider="openai", model="text-embedding-3-small", api_key="sk-test")
        result = svc.embed_batch(["rain", "snow"])
        assert len(result) == 2

    def test_from_config(self):
        from app.config import AppConfig
        cfg = AppConfig()
        svc = EmbeddingService.from_config(cfg)
        assert svc.model == "text-embedding-3-small"
