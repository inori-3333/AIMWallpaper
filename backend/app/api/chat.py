import asyncio
import json
import logging
import re
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.ai_engine import AIEngine
from app.core.image_separator import separate_foreground
from app.config import config
from app.db.database import get_session
from app.db.models import ChatMessage

logger = logging.getLogger(__name__)
router = APIRouter()

WALLPAPER_SYSTEM_PROMPT = """You are AIMWallpaper, an AI assistant that helps users create dynamic wallpapers for Wallpaper Engine.

You help users by:
1. Understanding their wallpaper requirements (effects, interactions, components)
2. Suggesting effects from the knowledge base
3. Building scene configurations
4. Generating SceneScript code for custom effects
5. Separating image foreground and background layers

You have the ability to separate foreground and background layers from an image.
When a user asks you to extract/separate/mat a person from an image, include the following JSON in your response:
{{"tool": "separate_layers", "asset_id": "..."}}
Use the asset_id from the available assets list below.

Available assets:
{asset_list}

Be conversational and ask clarifying questions when the user's intent is unclear.
Respond in the same language the user uses."""

_TOOL_CALL_RE = re.compile(
    r'```(?:json)?\s*(\{[^{}]*"tool"\s*:\s*"separate_layers"[^{}]*\})\s*```'
    r'|(\{[^{}]*"tool"\s*:\s*"separate_layers"[^{}]*\})'
)


def _build_system_prompt(assets: list[dict]) -> str:
    asset_list = json.dumps(
        [{"asset_id": a["asset_id"], "filename": a["filename"]} for a in assets],
        ensure_ascii=False,
    )
    return WALLPAPER_SYSTEM_PROMPT.format(asset_list=asset_list)


def _extract_tool_call(text: str) -> dict | None:
    match = _TOOL_CALL_RE.search(text)
    if not match:
        return None
    raw = match.group(1) or match.group(2)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if data.get("tool") != "separate_layers" or "asset_id" not in data:
        return None
    return data


def _strip_tool_call(text: str) -> str:
    text = re.sub(
        r'```(?:json)?\s*\{[^{}]*"tool"\s*:\s*"separate_layers"[^{}]*\}\s*```',
        "",
        text,
    )
    text = re.sub(
        r'\{[^{}]*"tool"\s*:\s*"separate_layers"[^{}]*\}',
        "",
        text,
    )
    return text.strip()


def _load_asset_index() -> list[dict]:
    index_path = Path(config.storage.data_dir) / "uploads" / "assets.json"
    if index_path.exists():
        try:
            return json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("Corrupted assets.json at %s", index_path)
            return []
    return []


def _get_ai_engine() -> AIEngine:
    return AIEngine.from_config(config)


def _load_history(project_id: str) -> list[dict]:
    with get_session() as session:
        rows = (
            session.query(ChatMessage)
            .filter(ChatMessage.project_id == project_id)
            .order_by(ChatMessage.created_at)
            .all()
        )
        return [{"role": r.role, "content": r.content} for r in rows]


def _save_message(project_id: str, role: str, content: str):
    with get_session() as session:
        session.add(ChatMessage(project_id=project_id, role=role, content=content))
        session.commit()


def _assemble_layers(project_id: str, sep_result: dict):
    """Use SceneBuilder to create bg + fg layers and pack into scene.pkg."""
    from app.core.scene_builder import SceneBuilder
    from app.core.project_generator import ProjectGenerator

    builder = SceneBuilder()
    builder.add_layer(name=sep_result["bg_layer_name"], image=sep_result["bg_stored_name"])
    builder.add_layer(name=sep_result["fg_layer_name"], image=sep_result["fg_stored_name"])

    generator = ProjectGenerator(
        output_dir=str(Path(config.storage.data_dir) / "projects"),
        assets_dir=str(Path(config.storage.data_dir) / "uploads"),
    )
    generator.generate(
        project_id=project_id,
        title=project_id,
        scene_builder=builder,
    )


async def _handle_tool_call(tool_data: dict, websocket: WebSocket, project_id: str):
    asset_id = tool_data["asset_id"]
    uploads_dir = Path(config.storage.data_dir) / "uploads"
    api_key = config.remove_bg.api_key

    if not api_key:
        await websocket.send_json({
            "type": "error",
            "code": "CONFIG_ERROR",
            "message": "remove.bg API key not configured. Please set remove_bg.api_key in config.yaml.",
        })
        return None

    await websocket.send_json({"type": "ai_thinking", "content": "Separating foreground and background..."})

    result = await asyncio.to_thread(
        separate_foreground, asset_id, api_key, uploads_dir
    )

    await asyncio.to_thread(_assemble_layers, project_id, result)

    return result


@router.websocket("/ws/chat/{project_id}")
async def chat_websocket(websocket: WebSocket, project_id: str):
    await websocket.accept()

    history = _load_history(project_id)

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
                _save_message(project_id, "user", content)

                await websocket.send_json({"type": "ai_thinking", "content": "Processing your request..."})

                try:
                    engine = _get_ai_engine()
                    assets = _load_asset_index()
                    system_prompt = _build_system_prompt(assets)

                    response = engine.chat(
                        system_prompt=system_prompt,
                        messages=history,
                    )
                    history.append({"role": "assistant", "content": response})
                    _save_message(project_id, "assistant", response)

                    tool_call = _extract_tool_call(response)
                    if tool_call:
                        try:
                            result = await _handle_tool_call(tool_call, websocket, project_id)
                            if result:
                                await websocket.send_json({"type": "layer_separated", "data": result})
                        except FileNotFoundError as e:
                            await websocket.send_json({"type": "error", "code": "ASSET_NOT_FOUND", "message": str(e)})
                        except ValueError as e:
                            await websocket.send_json({"type": "error", "code": "INVALID_FORMAT", "message": str(e)})
                        except Exception as e:
                            logger.error("Layer separation error: %s", e)
                            await websocket.send_json({"type": "error", "code": "SEPARATION_ERROR", "message": f"Failed to separate layers: {e}"})

                        display_text = _strip_tool_call(response)
                    else:
                        display_text = response

                    await websocket.send_json({"type": "ai_message", "content": display_text})
                except Exception as e:
                    logger.error("Chat error: %s", e)
                    await websocket.send_json({"type": "error", "code": "LLM_ERROR", "message": str(e)})
            else:
                await websocket.send_json({"type": "error", "code": "UNKNOWN_TYPE", "message": f"Unknown message type: {msg_type}"})

    except WebSocketDisconnect:
        logger.info("Client disconnected from chat/%s", project_id)
