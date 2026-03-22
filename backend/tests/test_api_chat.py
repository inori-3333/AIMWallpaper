import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestChatWebSocket:
    @patch("app.api.chat._get_ai_engine")
    def test_websocket_connect_and_send(self, mock_get_engine, client):
        mock_engine = MagicMock()
        mock_engine.chat.return_value = "I can help with that wallpaper!"
        mock_get_engine.return_value = mock_engine

        with client.websocket_connect("/ws/chat/1") as ws:
            ws.send_json({"type": "user_message", "content": "Add rain effect"})
            response = ws.receive_json()
            assert response["type"] in ("ai_thinking", "ai_message")
            # Read all messages until we get ai_message
            messages = [response]
            while response["type"] != "ai_message":
                response = ws.receive_json()
                messages.append(response)
            assert any(m["type"] == "ai_message" for m in messages)

    @patch("app.api.chat._get_ai_engine")
    def test_websocket_conversation_history(self, mock_get_engine, client):
        mock_engine = MagicMock()
        mock_engine.chat.return_value = "Response"
        mock_get_engine.return_value = mock_engine

        with client.websocket_connect("/ws/chat/1") as ws:
            ws.send_json({"type": "user_message", "content": "Hello"})
            # Drain messages
            while True:
                msg = ws.receive_json()
                if msg["type"] == "ai_message":
                    break

            ws.send_json({"type": "user_message", "content": "Follow up"})
            while True:
                msg = ws.receive_json()
                if msg["type"] == "ai_message":
                    break

            # Verify history was accumulated (2 user messages in second call)
            assert mock_engine.chat.call_count == 2
            second_call = mock_engine.chat.call_args_list[1]
            messages = second_call.kwargs.get("messages") or second_call[1].get("messages") or second_call[0][1]
            assert len(messages) >= 2  # at least 2 user turns

    @patch("app.api.chat._get_ai_engine")
    def test_websocket_error_handling(self, mock_get_engine, client):
        mock_engine = MagicMock()
        mock_engine.chat.side_effect = Exception("LLM timeout")
        mock_get_engine.return_value = mock_engine

        with client.websocket_connect("/ws/chat/1") as ws:
            ws.send_json({"type": "user_message", "content": "test"})
            # Should get thinking then error
            messages = []
            for _ in range(5):
                try:
                    msg = ws.receive_json()
                    messages.append(msg)
                    if msg["type"] == "error":
                        break
                except Exception:
                    break
            assert any(m["type"] == "error" for m in messages)

    @patch("app.api.chat._get_ai_engine")
    def test_websocket_invalid_message(self, mock_get_engine, client):
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        with client.websocket_connect("/ws/chat/1") as ws:
            ws.send_text("not valid json {{{")
            msg = ws.receive_json()
            assert msg["type"] == "error"
