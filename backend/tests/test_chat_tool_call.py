import json
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

import pytest


class TestExtractToolCall:
    def test_plain_tool_call(self):
        from app.api.chat import _extract_tool_call

        text = 'I will separate the layers. {"tool": "separate_layers", "asset_id": "abc-123"}'
        result = _extract_tool_call(text)
        assert result is not None
        assert result["tool"] == "separate_layers"
        assert result["asset_id"] == "abc-123"

    def test_tool_call_in_code_block(self):
        from app.api.chat import _extract_tool_call

        text = 'Here is the operation:\n```json\n{"tool": "separate_layers", "asset_id": "abc-123"}\n```'
        result = _extract_tool_call(text)
        assert result is not None
        assert result["asset_id"] == "abc-123"

    def test_no_tool_call(self):
        from app.api.chat import _extract_tool_call

        text = "Sure, I can help you with that wallpaper effect."
        result = _extract_tool_call(text)
        assert result is None

    def test_malformed_json(self):
        from app.api.chat import _extract_tool_call

        text = '{"tool": "separate_layers", asset_id: broken}'
        result = _extract_tool_call(text)
        assert result is None

    def test_missing_asset_id(self):
        from app.api.chat import _extract_tool_call

        text = '{"tool": "separate_layers"}'
        result = _extract_tool_call(text)
        assert result is None


class TestStripToolCall:
    def test_strip_inline(self):
        from app.api.chat import _strip_tool_call

        text = 'I will do it. {"tool": "separate_layers", "asset_id": "x"} Done.'
        result = _strip_tool_call(text)
        assert "separate_layers" not in result
        assert "I will do it." in result
        assert "Done." in result

    def test_strip_code_block(self):
        from app.api.chat import _strip_tool_call

        text = 'Separating:\n```json\n{"tool": "separate_layers", "asset_id": "x"}\n```\nDone.'
        result = _strip_tool_call(text)
        assert "separate_layers" not in result


class TestBuildSystemPrompt:
    def test_includes_asset_list(self):
        from app.api.chat import _build_system_prompt

        assets = [{"asset_id": "a1", "filename": "photo.png"}]
        prompt = _build_system_prompt(assets)
        assert "a1" in prompt
        assert "photo.png" in prompt
        assert "separate_layers" in prompt

    def test_empty_assets(self):
        from app.api.chat import _build_system_prompt

        prompt = _build_system_prompt([])
        assert "separate_layers" in prompt
        assert "[]" in prompt


class TestHandleToolCall:
    @pytest.mark.asyncio
    async def test_missing_api_key(self):
        from app.api.chat import _handle_tool_call

        ws = AsyncMock()

        with patch("app.api.chat.config") as mock_config:
            mock_config.remove_bg.api_key = ""
            mock_config.storage.data_dir = "/tmp"
            result = await _handle_tool_call({"asset_id": "x"}, ws, "proj-1")

        assert result is None
        ws.send_json.assert_called()
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["code"] == "CONFIG_ERROR"

    @pytest.mark.asyncio
    async def test_successful_separation(self, tmp_path):
        from app.api.chat import _handle_tool_call

        ws = AsyncMock()
        sep_result = {
            "foreground_asset_id": "fg-1",
            "background_asset_id": "bg-1",
            "fg_layer_name": "foreground",
            "bg_layer_name": "background",
            "fg_stored_name": "fg-1.png",
            "bg_stored_name": "bg-1.png",
        }

        with patch("app.api.chat.config") as mock_config, \
             patch("app.api.chat.separate_foreground", return_value=sep_result), \
             patch("app.api.chat.asyncio") as mock_asyncio:
            mock_config.remove_bg.api_key = "test-key"
            mock_config.storage.data_dir = str(tmp_path)
            mock_asyncio.to_thread = AsyncMock(side_effect=[sep_result, None])

            result = await _handle_tool_call({"asset_id": "bg-1"}, ws, "proj-1")

        assert result == sep_result

        # Verify to_thread was called twice: once for separate_foreground, once for _assemble_layers
        assert mock_asyncio.to_thread.call_count == 2
        # Second call should be _assemble_layers with project_id and sep_result
        second_call = mock_asyncio.to_thread.call_args_list[1]
        assert second_call[0][1] == "proj-1"  # project_id
        assert second_call[0][2] == sep_result  # sep_result
