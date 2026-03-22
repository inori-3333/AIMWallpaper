import pytest
from unittest.mock import patch, MagicMock
from app.core.ai_engine import AIEngine


class TestAIEngine:
    def test_build_model_string_openai(self):
        engine = AIEngine(provider="openai", model="gpt-4o", api_key="sk-test")
        assert engine._model_string() == "gpt-4o"

    def test_build_model_string_anthropic(self):
        engine = AIEngine(provider="anthropic", model="claude-sonnet-4-20250514", api_key="sk-test")
        assert engine._model_string() == "claude-sonnet-4-20250514"

    def test_build_model_string_ollama(self):
        engine = AIEngine(provider="ollama", model="llama3", base_url="http://localhost:11434")
        assert engine._model_string() == "ollama/llama3"

    @patch("app.core.ai_engine.litellm_completion")
    def test_chat_completion(self, mock_completion):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! I can help with wallpapers."
        mock_completion.return_value = mock_response
        engine = AIEngine(provider="openai", model="gpt-4o", api_key="sk-test")
        result = engine.chat(system_prompt="You are a wallpaper assistant.", messages=[{"role": "user", "content": "Hi"}])
        assert result == "Hello! I can help with wallpapers."
        mock_completion.assert_called_once()

    @patch("app.core.ai_engine.litellm_completion")
    def test_chat_with_retries_on_timeout(self, mock_completion):
        mock_completion.side_effect = [Exception("timeout"), MagicMock(choices=[MagicMock(message=MagicMock(content="OK"))])]
        engine = AIEngine(provider="openai", model="gpt-4o", api_key="sk-test")
        result = engine.chat(system_prompt="test", messages=[{"role": "user", "content": "test"}])
        assert result == "OK"
        assert mock_completion.call_count == 2

    @patch("app.core.ai_engine.litellm_completion")
    def test_chat_max_retries_exceeded(self, mock_completion):
        mock_completion.side_effect = Exception("timeout")
        engine = AIEngine(provider="openai", model="gpt-4o", api_key="sk-test")
        with pytest.raises(Exception, match="timeout"):
            engine.chat(system_prompt="test", messages=[{"role": "user", "content": "test"}])
        assert mock_completion.call_count == 3

    def test_from_config(self):
        from app.config import AppConfig
        cfg = AppConfig()
        engine = AIEngine.from_config(cfg)
        assert engine.provider == "openai"
        assert engine.model == "gpt-4o"
