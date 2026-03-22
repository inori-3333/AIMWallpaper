# Image Layer Separation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add AI-driven foreground/background separation via remove.bg API, triggered through the chat interface.

**Architecture:** New `core/image_separator.py` module handles the remove.bg API call and asset registration. Chat handler detects tool calls in AI responses, invokes the separator, assembles layers via SceneBuilder, and packs into scene.pkg via ProjectGenerator.

**Tech Stack:** Python 3.11+, FastAPI, httpx, remove.bg REST API, existing SceneBuilder/ProjectGenerator

**Spec:** `docs/superpowers/specs/2026-03-22-image-layer-separation-design.md`

---

## File Structure

| File | Role |
|------|------|
| `backend/app/config.py` | Add `RemoveBgConfig` to `AppConfig` |
| `config.yaml` | Already has `remove_bg.api_key` (uncommitted change) |
| `backend/app/core/image_separator.py` | **New** — `separate_foreground()` function |
| `backend/app/api/chat.py` | Tool call detection, asset context injection, layer assembly |
| `backend/pyproject.toml` | Move `httpx` to main deps |
| `backend/tests/test_image_separator.py` | **New** — unit tests for separator |
| `backend/tests/test_chat_tool_call.py` | **New** — unit tests for tool call detection + handler |

**Note:** `config.yaml` already has `remove_bg.api_key` and `config.py` already has `mosaic`/`deepseek` additions in the working tree (uncommitted). Task 1 builds on top of that state.

---

### Task 1: Configuration — RemoveBgConfig

**Files:**
- Modify: `backend/app/config.py` — add `RemoveBgConfig` class and field in `AppConfig`
- Test: `backend/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

In `backend/tests/test_config.py`, add:

```python
def test_remove_bg_config():
    from app.config import AppConfig
    cfg = AppConfig()
    assert hasattr(cfg, "remove_bg")
    assert cfg.remove_bg.api_key == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_config.py::test_remove_bg_config -v`
Expected: FAIL with `AttributeError: 'AppConfig' object has no attribute 'remove_bg'`

- [ ] **Step 3: Implement RemoveBgConfig**

In `backend/app/config.py`, add after `EmbeddingConfig` class:

```python
class RemoveBgConfig(BaseModel):
    api_key: str = ""
```

In `AppConfig`, add field:

```python
    remove_bg: RemoveBgConfig = RemoveBgConfig()
```

`config.yaml` already has the `remove_bg` section — no changes needed there.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_config.py::test_remove_bg_config -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/tests/test_config.py
git commit -m "feat: add RemoveBgConfig to app configuration"
```

---

### Task 2: Move httpx to main dependencies

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Move httpx from dev to main dependencies**

In `backend/pyproject.toml`, add `"httpx>=0.27.0",` to `dependencies` (after `"mss>=9.0.0",`) and remove it from `dev` optional dependencies.

Result:

```toml
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "sqlalchemy>=2.0.0",
    "aiofiles>=24.0.0",
    "pillow>=10.0.0",
    "python-multipart>=0.0.9",
    "pyyaml>=6.0",
    "litellm>=1.40.0",
    "chromadb>=0.5.0",
    "websockets>=12.0",
    "mss>=9.0.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
]
```

- [ ] **Step 2: Verify import works**

Run: `cd backend && python -c "import httpx; print(httpx.__version__)"`
Expected: prints version number without error

- [ ] **Step 3: Commit**

```bash
git add backend/pyproject.toml
git commit -m "build: move httpx from dev to main dependencies"
```

---

### Task 3: Core — image_separator module

**Files:**
- Create: `backend/app/core/image_separator.py`
- Test: `backend/tests/test_image_separator.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_image_separator.py`:

```python
import json
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


@pytest.fixture
def uploads_dir(tmp_path):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    return uploads


@pytest.fixture
def asset_with_image(uploads_dir):
    """Create a fake asset entry and image file, return asset_id."""
    asset_id = str(uuid.uuid4())
    stored_name = f"{asset_id}.png"
    (uploads_dir / stored_name).write_bytes(FAKE_PNG)
    index = [
        {
            "asset_id": asset_id,
            "filename": "photo.png",
            "stored_name": stored_name,
            "content_type": "image/png",
            "size": len(FAKE_PNG),
        }
    ]
    (uploads_dir / "assets.json").write_text(json.dumps(index), encoding="utf-8")
    return asset_id


class TestSeparateForeground:
    def test_success(self, uploads_dir, asset_with_image):
        from app.core.image_separator import separate_foreground

        fg_png = b"\x89PNG\r\n\x1a\nFOREGROUND"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = fg_png

        with patch("app.core.image_separator.httpx.post", return_value=mock_response):
            result = separate_foreground(
                asset_id=asset_with_image,
                api_key="test-key",
                uploads_dir=uploads_dir,
            )

        assert result["background_asset_id"] == asset_with_image
        assert result["foreground_asset_id"] != asset_with_image
        assert result["fg_layer_name"] == "foreground"
        assert result["bg_layer_name"] == "background"

        # Verify foreground file was saved
        fg_id = result["foreground_asset_id"]
        fg_file = uploads_dir / f"{fg_id}.png"
        assert fg_file.exists()
        assert fg_file.read_bytes() == fg_png

        # Verify asset index was updated
        index = json.loads((uploads_dir / "assets.json").read_text(encoding="utf-8"))
        fg_entries = [a for a in index if a["asset_id"] == fg_id]
        assert len(fg_entries) == 1
        assert "foreground" in fg_entries[0]["filename"]

    def test_asset_not_found(self, uploads_dir):
        from app.core.image_separator import separate_foreground

        (uploads_dir / "assets.json").write_text("[]", encoding="utf-8")

        with pytest.raises(FileNotFoundError, match="not found"):
            separate_foreground(
                asset_id="nonexistent",
                api_key="test-key",
                uploads_dir=uploads_dir,
            )

    def test_api_failure(self, uploads_dir, asset_with_image):
        from app.core.image_separator import separate_foreground

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Invalid API key"
        mock_response.raise_for_status = MagicMock(
            side_effect=Exception("403 Forbidden")
        )

        with patch("app.core.image_separator.httpx.post", return_value=mock_response):
            with pytest.raises(Exception, match="403"):
                separate_foreground(
                    asset_id=asset_with_image,
                    api_key="bad-key",
                    uploads_dir=uploads_dir,
                )

    def test_unsupported_format(self, uploads_dir):
        """Non-image files should be rejected before calling remove.bg."""
        from app.core.image_separator import separate_foreground

        asset_id = str(uuid.uuid4())
        stored_name = f"{asset_id}.txt"
        (uploads_dir / stored_name).write_bytes(b"not an image")
        index = [{
            "asset_id": asset_id,
            "filename": "notes.txt",
            "stored_name": stored_name,
            "content_type": "text/plain",
            "size": 12,
        }]
        (uploads_dir / "assets.json").write_text(json.dumps(index), encoding="utf-8")

        with pytest.raises(ValueError, match="Unsupported image format"):
            separate_foreground(
                asset_id=asset_id,
                api_key="test-key",
                uploads_dir=uploads_dir,
            )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_image_separator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.core.image_separator'`

- [ ] **Step 3: Implement image_separator.py**

Create `backend/app/core/image_separator.py`:

```python
import json
import uuid
from pathlib import Path

import httpx

REMOVE_BG_URL = "https://api.remove.bg/v1.0/removebg"
ASSET_INDEX_FILE = "assets.json"
SUPPORTED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/bmp", "image/tga"}


def _load_index(uploads_dir: Path) -> list[dict]:
    index_path = uploads_dir / ASSET_INDEX_FILE
    if index_path.exists():
        return json.loads(index_path.read_text(encoding="utf-8"))
    return []


def _save_index(uploads_dir: Path, assets: list[dict]):
    index_path = uploads_dir / ASSET_INDEX_FILE
    index_path.write_text(json.dumps(assets, ensure_ascii=False, indent=2), encoding="utf-8")


def separate_foreground(asset_id: str, api_key: str, uploads_dir: Path) -> dict:
    """Call remove.bg to extract foreground from an image asset.

    Returns dict with foreground_asset_id, background_asset_id,
    fg_layer_name, bg_layer_name.

    Raises:
        FileNotFoundError: if asset_id is not in the index.
        ValueError: if the asset is not a supported image format.
    """
    assets = _load_index(uploads_dir)
    target = None
    for a in assets:
        if a["asset_id"] == asset_id:
            target = a
            break
    if target is None:
        raise FileNotFoundError(f"Asset '{asset_id}' not found in index")

    if target.get("content_type", "") not in SUPPORTED_IMAGE_TYPES:
        raise ValueError(
            f"Unsupported image format: {target.get('content_type', 'unknown')}. "
            "Please upload a PNG or JPG image."
        )

    image_path = uploads_dir / target["stored_name"]
    image_bytes = image_path.read_bytes()

    response = httpx.post(
        REMOVE_BG_URL,
        headers={"X-Api-Key": api_key},
        files={"image_file": (target["stored_name"], image_bytes, target["content_type"])},
        data={"size": "auto"},
        timeout=60.0,
    )
    response.raise_for_status()

    fg_id = str(uuid.uuid4())
    fg_stored_name = f"{fg_id}.png"
    (uploads_dir / fg_stored_name).write_bytes(response.content)

    original_name = Path(target["filename"]).stem
    fg_entry = {
        "asset_id": fg_id,
        "filename": f"{original_name}_foreground.png",
        "stored_name": fg_stored_name,
        "content_type": "image/png",
        "size": len(response.content),
    }
    assets.append(fg_entry)
    _save_index(uploads_dir, assets)

    return {
        "foreground_asset_id": fg_id,
        "background_asset_id": asset_id,
        "fg_layer_name": "foreground",
        "bg_layer_name": "background",
        "fg_stored_name": fg_stored_name,
        "bg_stored_name": target["stored_name"],
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_image_separator.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/image_separator.py backend/tests/test_image_separator.py
git commit -m "feat: add image_separator module with remove.bg integration"
```

---

### Task 4: Chat handler — tool call detection and layer assembly

**Files:**
- Create: `backend/tests/test_chat_tool_call.py`
- Modify: `backend/app/api/chat.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_chat_tool_call.py`:

```python
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
            mock_asyncio.to_thread = AsyncMock(return_value=sep_result)

            result = await _handle_tool_call({"asset_id": "bg-1"}, ws, "proj-1")

        assert result == sep_result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_chat_tool_call.py -v`
Expected: FAIL with `ImportError: cannot import name '_extract_tool_call'`

- [ ] **Step 3: Implement chat.py changes**

Replace `backend/app/api/chat.py` entirely:

```python
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
        return json.loads(index_path.read_text(encoding="utf-8"))
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
```

**Key differences from old chat.py:**
- Removed unused `get_engine` import (was unused in original)
- Added `_build_system_prompt()` with asset context injection
- Added `_extract_tool_call()` and `_strip_tool_call()` for tool call parsing
- Added `_handle_tool_call()` with `asyncio.to_thread()` to avoid blocking
- Added `_assemble_layers()` that calls `SceneBuilder.add_layer()` twice then `ProjectGenerator.generate()` to pack into `scene.pkg`
- Added `ValueError` handler for unsupported image format errors

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_chat_tool_call.py -v`
Expected: 10 passed

- [ ] **Step 5: Run all existing tests to check for regressions**

Run: `cd backend && python -m pytest tests/ -v`
Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/chat.py backend/tests/test_chat_tool_call.py
git commit -m "feat: add tool call detection, layer assembly, and separation to chat handler"
```

---

### Task 5: Integration smoke test

**Files:**
- Create: `backend/tests/test_separation_integration.py`

- [ ] **Step 1: Write integration test**

Create `backend/tests/test_separation_integration.py`:

```python
"""Integration test: full flow from asset creation through separation and layer assembly."""

import json
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
FAKE_FG_PNG = b"\x89PNG\r\n\x1a\nFOREGROUND_RESULT"


@pytest.fixture
def populated_uploads(tmp_data_dir):
    """Create uploads dir with one image asset, return (asset_id, uploads_dir)."""
    uploads = tmp_data_dir / "uploads"
    asset_id = str(uuid.uuid4())
    stored = f"{asset_id}.png"
    (uploads / stored).write_bytes(FAKE_PNG)
    index = [{
        "asset_id": asset_id,
        "filename": "test_photo.jpg",
        "stored_name": stored,
        "content_type": "image/jpeg",
        "size": len(FAKE_PNG),
    }]
    (uploads / "assets.json").write_text(json.dumps(index), encoding="utf-8")
    return asset_id, uploads


class TestSeparationIntegration:
    def test_full_separation_flow(self, populated_uploads):
        """Test: separate_foreground creates fg asset and updates index."""
        asset_id, uploads = populated_uploads

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = FAKE_FG_PNG
        mock_response.raise_for_status = MagicMock()

        with patch("app.core.image_separator.httpx.post", return_value=mock_response):
            from app.core.image_separator import separate_foreground
            result = separate_foreground(
                asset_id=asset_id,
                api_key="test-key",
                uploads_dir=uploads,
            )

        # Both assets exist in index
        index = json.loads((uploads / "assets.json").read_text(encoding="utf-8"))
        assert len(index) == 2

        bg_entry = next(a for a in index if a["asset_id"] == result["background_asset_id"])
        fg_entry = next(a for a in index if a["asset_id"] == result["foreground_asset_id"])

        assert bg_entry["filename"] == "test_photo.jpg"
        assert "foreground" in fg_entry["filename"]

        # Foreground file exists on disk
        fg_path = uploads / fg_entry["stored_name"]
        assert fg_path.exists()
        assert fg_path.read_bytes() == FAKE_FG_PNG

        # Result includes stored_name fields for layer assembly
        assert result["fg_stored_name"] == fg_entry["stored_name"]
        assert result["bg_stored_name"] == bg_entry["stored_name"]

    def test_layer_assembly(self, populated_uploads, tmp_data_dir):
        """Test: _assemble_layers creates scene.pkg with both layers."""
        asset_id, uploads = populated_uploads

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = FAKE_FG_PNG
        mock_response.raise_for_status = MagicMock()

        with patch("app.core.image_separator.httpx.post", return_value=mock_response):
            from app.core.image_separator import separate_foreground
            result = separate_foreground(
                asset_id=asset_id,
                api_key="test-key",
                uploads_dir=uploads,
            )

        # Create projects dir
        projects_dir = tmp_data_dir / "projects"
        projects_dir.mkdir(exist_ok=True)

        from app.core.scene_builder import SceneBuilder
        from app.core.project_generator import ProjectGenerator

        builder = SceneBuilder()
        builder.add_layer(name=result["bg_layer_name"], image=result["bg_stored_name"])
        builder.add_layer(name=result["fg_layer_name"], image=result["fg_stored_name"])

        generator = ProjectGenerator(
            output_dir=str(projects_dir),
            assets_dir=str(uploads),
        )
        project_dir = generator.generate(
            project_id="test-project",
            title="test-project",
            scene_builder=builder,
        )

        # Verify scene.pkg and project.json were created
        assert (project_dir / "scene.pkg").exists()
        assert (project_dir / "project.json").exists()

        # Verify scene.pkg contains scene.json with both layers
        from app.core.scene_packager import unpack
        pkg_files = unpack((project_dir / "scene.pkg").read_bytes())
        assert "scene.json" in pkg_files
        scene = json.loads(pkg_files["scene.json"])
        layer_names = [obj["name"] for obj in scene["objects"]]
        assert "background" in layer_names
        assert "foreground" in layer_names
        assert layer_names.index("background") < layer_names.index("foreground")
```

- [ ] **Step 2: Run integration tests**

Run: `cd backend && python -m pytest tests/test_separation_integration.py -v`
Expected: 2 passed

- [ ] **Step 3: Run full test suite**

Run: `cd backend && python -m pytest tests/ -v`
Expected: all pass

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_separation_integration.py
git commit -m "test: add integration tests for separation flow and layer assembly"
```
