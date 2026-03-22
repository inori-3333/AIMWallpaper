# Image Layer Separation (Foreground/Background) Design

## Overview

Add AI-driven foreground/background separation to AIMWallpaper. Users instruct the AI via chat to separate a person from the background of an uploaded image. The system calls the remove.bg cloud API to produce a transparent-background foreground PNG, then registers both layers (original as background, extracted as foreground) into the wallpaper project for use in Wallpaper Engine.

## User Flow

1. User uploads an image via the asset upload endpoint.
2. In the chat, user asks the AI to separate/extract the person from the image.
3. AI recognizes the intent and emits a structured tool call in its response: `{"tool": "separate_layers", "asset_id": "..."}`.
4. The chat handler detects the tool call, invokes `separate_foreground(asset_id)`.
5. The method calls remove.bg, saves the foreground PNG, registers it as a new asset.
6. Two layers are available: background (original image) + foreground (extracted PNG).
7. The chat handler calls `SceneBuilder.add_layer()` twice (background first, then foreground) and triggers `ProjectGenerator.generate()` to pack the layers into `scene.pkg`.
8. The result is sent back to the user via WebSocket.

## Technical Design

### Configuration

Add to `config.yaml`:

```yaml
remove_bg:
  api_key: "your-api-key-here"
```

Add to `config.py`:

```python
class RemoveBgConfig(BaseModel):
    api_key: str = ""
```

Add `remove_bg: RemoveBgConfig = RemoveBgConfig()` to `AppConfig`.

### New Module: `core/image_separator.py`

A standalone module (not on `AIEngine`) to keep single responsibility. `AIEngine` stays focused on LLM calls.

```python
def separate_foreground(asset_id: str, api_key: str, uploads_dir: Path) -> dict
```

1. Look up `asset_id` in the asset index (`data/uploads/assets.json`).
2. Read the image file bytes from `data/uploads/`.
3. POST to `https://api.remove.bg/v1.0/removebg`:
   - Header: `X-Api-Key: <api_key>`
   - Body: `multipart/form-data` with `image_file` and `size=auto`
   - Response: 200 -> raw PNG bytes (foreground with transparent background)
4. Generate a new UUID for the foreground image, save as `<uuid>.png` in uploads (consistent with existing asset ID generation in `assets.py`).
5. Register the new asset in `assets.json` (filename suffixed with `_foreground`).
6. Return `{"foreground_asset_id": "...", "background_asset_id": "<original>", "fg_layer_name": "foreground", "bg_layer_name": "background"}`.

Uses `httpx` synchronous client, wrapped in `asyncio.to_thread()` at the call site in `chat.py` to avoid blocking the async event loop.

### Chat Handler Changes (`chat.py`)

**Asset context injection:**

Before sending messages to the AI, inject the current asset list into the system prompt so the AI knows which `asset_id` values are available:

```
Available assets: [{"asset_id": "xxx", "filename": "photo.jpg"}, ...]
```

**System prompt addition:**

> You have the ability to separate foreground and background layers from an image. When a user asks you to extract/separate/mat a person from an image, include `{"tool": "separate_layers", "asset_id": "..."}` in your response. Use the asset_id from the available assets list above.

**Tool call detection:**

Use `json.loads()` on regex-matched `\{[^{}]*"tool"\s*:\s*"separate_layers"[^{}]*\}` blocks. If the JSON is malformed or `asset_id` is missing, return an error message to the user. Also handle the case where the AI wraps the JSON in a markdown code block.

**Response processing — layer assembly:**

After `separate_foreground()` returns successfully:

1. Load or create a `SceneBuilder` for the current project.
2. Call `builder.add_layer(name="background", image=<bg_stored_name>)` — added first (bottom layer).
3. Call `builder.add_layer(name="foreground", image=<fg_stored_name>)` — added second (top layer, renders in front).
4. Wallpaper Engine renders objects in list order; the foreground layer on top covers the person in the background. No explicit z-index needed — list position determines stacking.
5. Trigger `ProjectGenerator.generate()` to pack into `scene.pkg`.
6. Send the execution result via WebSocket as a structured message.
7. Send the text portion of the AI response (with JSON block stripped) as the display message.

### Error Handling

| Scenario | Behavior |
|----------|----------|
| `asset_id` not found | Return error message to user via WebSocket |
| remove.bg API failure (auth, rate limit, server error) | Return error message suggesting user check API key or retry |
| Unsupported image format | Prompt user to upload PNG/JPG |
| Malformed tool call JSON / missing `asset_id` | Return error message asking AI to retry with correct format |

### Dependencies

Move `httpx` from dev to main dependencies in `pyproject.toml` (it is already present under `[project.optional-dependencies] dev`).

### Files Changed

| File | Change |
|------|--------|
| `config.yaml` | Add `remove_bg.api_key` |
| `backend/app/config.py` | Add `RemoveBgConfig` model + field in `AppConfig` |
| `backend/app/core/image_separator.py` | **New file** — `separate_foreground()` function |
| `backend/app/api/chat.py` | Update system prompt (add asset context + layer separation capability); add tool call detection + execution; add layer assembly logic |
| `backend/pyproject.toml` | Move `httpx` from dev to main dependencies |

### Not Changed

- `SceneBuilder` / `ProjectGenerator` / `scene_packager.py` — existing `add_layer()` and `scene.pkg` packing logic already supports the needed operations. Called from `chat.py` after separation.

## Known Limitations

- **Concurrency**: `assets.json` file I/O has no locking. This is a pre-existing issue; not addressed in this feature.
- **remove.bg free tier**: 50 calls/month. No client-side usage tracking in this phase.
- **Blocking concern**: The synchronous `engine.chat()` call in `chat.py` already blocks the event loop. The `separate_foreground()` call will use `asyncio.to_thread()` to avoid adding to this problem.

## Background Layer Strategy

Phase 1 (this design): Use the original image as-is for the background layer. The foreground layer sits on top and visually covers the person in the background.

Phase 2 (future): Add inpainting to fill the person-shaped hole in the background for cleaner parallax effects.
