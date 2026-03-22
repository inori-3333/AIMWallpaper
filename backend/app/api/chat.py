import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.ai_engine import AIEngine
from app.config import config

logger = logging.getLogger(__name__)
router = APIRouter()

WALLPAPER_SYSTEM_PROMPT = """You are AIMWallpaper, an AI assistant that helps users create dynamic wallpapers for Wallpaper Engine.

You help users by:
1. Understanding their wallpaper requirements (effects, interactions, components)
2. Suggesting effects from the knowledge base
3. Building scene.json configurations
4. Generating SceneScript code for custom effects

Be conversational and ask clarifying questions when the user's intent is unclear.
Respond in the same language the user uses."""


def _get_ai_engine() -> AIEngine:
    return AIEngine.from_config(config)


# In-memory session storage (single-user app)
_sessions: dict[str, list[dict]] = {}


@router.websocket("/ws/chat/{project_id}")
async def chat_websocket(websocket: WebSocket, project_id: str):
    await websocket.accept()

    if project_id not in _sessions:
        _sessions[project_id] = []

    history = _sessions[project_id]

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "code": "INVALID_JSON", "message": "Invalid JSON message"})
                continue

            msg_type = data.get("type", "")
            content = data.get("content", "")

            if msg_type == "user_message" and content:
                history.append({"role": "user", "content": content})

                # Send thinking indicator
                await websocket.send_json({"type": "ai_thinking", "content": "Processing your request..."})

                try:
                    engine = _get_ai_engine()
                    response = engine.chat(
                        system_prompt=WALLPAPER_SYSTEM_PROMPT,
                        messages=history,
                    )
                    history.append({"role": "assistant", "content": response})

                    await websocket.send_json({"type": "ai_message", "content": response})
                except Exception as e:
                    logger.error("Chat error: %s", e)
                    await websocket.send_json({"type": "error", "code": "LLM_ERROR", "message": str(e)})
            else:
                await websocket.send_json({"type": "error", "code": "UNKNOWN_TYPE", "message": f"Unknown message type: {msg_type}"})

    except WebSocketDisconnect:
        logger.info("Client disconnected from chat/%s", project_id)
