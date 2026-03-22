# Image Layer Separation (Foreground/Background) Design

## Overview

Add AI-driven foreground/background separation to AIMWallpaper. Users instruct the AI via chat to separate a person from the background of an uploaded image. The system calls the remove.bg cloud API to produce a transparent-background foreground PNG, then registers both layers (original as background, extracted as foreground) into the wallpaper project for use in Wallpaper Engine.

## User Flow

1. User uploads an image via the asset upload endpoint.
2. In the chat, user asks the AI to separate/extract the person from the image.
3. AI recognizes the intent and emits a structured tool call in its response: `{"tool": "separate_layers", "asset_id": "..."}`.
4. The chat handler detects the tool call, invokes `AIEngine.separate_foreground(asset_id)`.
5. The method calls remove.bg, saves the foreground PNG, registers it as a new asset.
6. Two layers are available: background (original image) + foreground (extracted PNG).
7. The result is sent back to the user via WebSocket. Layers are later assembled into `scene.pkg` via the existing `SceneBuilder` + `ProjectGenerator` pipeline.

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

### AIEngine Changes (`ai_engine.py`)

Add method `separate_foreground(asset_id: str) -> dict`:

1. Look up `asset_id` in the asset index (`data/uploads/assets.json`).
2. Read the image file bytes from `data/uploads/`.
3. POST to `https://api.remove.bg/v1.0/removebg`:
   - Header: `X-Api-Key: <api_key>`
   - Body: `multipart/form-data` with `image_file` and `size=auto`
   - Response: 200 -> raw PNG bytes (foreground with transparent background)
4. Generate a new `asset_id` for the foreground image, save as `<new_id>.png` in uploads.
5. Register the new asset in `assets.json` (filename suffixed with `_foreground`).
6. Return `{"foreground_asset_id": "...", "background_asset_id": "<original>", "fg_layer_name": "foreground", "bg_layer_name": "background"}`.

Uses `httpx` (synchronous) for the HTTP call, consistent with the existing synchronous `chat()` method style.

### Chat Handler Changes (`chat.py`)

**System prompt addition:**

> You have the ability to separate foreground and background layers from an image. When a user asks you to extract/separate/mat a person from an image, include `{"tool": "separate_layers", "asset_id": "..."}` in your response. Get the asset_id from the user's uploaded asset list.

**Response processing:**

After receiving the AI response, scan for `{"tool": "separate_layers", ...}` using regex. If found:

1. Extract `asset_id` from the JSON.
2. Call `engine.separate_foreground(asset_id)`.
3. Send the execution result (layer info) back via WebSocket as a structured message.
4. Send the text portion of the AI response (with JSON block stripped) as the display message.

### Error Handling

| Scenario | Behavior |
|----------|----------|
| `asset_id` not found | Return error message to user via WebSocket |
| remove.bg API failure (auth, rate limit, server error) | Return error message suggesting user check API key or retry |
| Unsupported image format | Prompt user to upload PNG/JPG |

### Dependencies

Add `httpx` to `pyproject.toml` dependencies.

### Files Changed

| File | Change |
|------|--------|
| `config.yaml` | Add `remove_bg.api_key` |
| `backend/app/config.py` | Add `RemoveBgConfig` model + field in `AppConfig` |
| `backend/app/core/ai_engine.py` | Add `separate_foreground()` method |
| `backend/app/api/chat.py` | Update system prompt; add tool call detection + execution |
| `backend/pyproject.toml` | Add `httpx` dependency |

### Not Changed

- `SceneBuilder` / `ProjectGenerator` / `scene_packager.py` — existing `add_layer()` and `scene.pkg` packing logic already supports the needed operations.

## Background Layer Strategy

Phase 1 (this design): Use the original image as-is for the background layer. The foreground layer sits on top and visually covers the person in the background.

Phase 2 (future): Add inpainting to fill the person-shaped hole in the background for cleaner parallax effects.
