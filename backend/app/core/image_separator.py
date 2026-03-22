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
    fg_layer_name, bg_layer_name, fg_stored_name, bg_stored_name.

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
