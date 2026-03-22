import uuid
import json
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import config
from app.models.api import AssetResponse

router = APIRouter(prefix="/api/assets", tags=["assets"])

ALLOWED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".tga",
    ".mp4", ".webm",
    ".ogg", ".mp3", ".wav",
    ".pkg", ".json",
}

ASSET_INDEX_FILE = "assets.json"


def _uploads_dir() -> Path:
    return Path(config.storage.data_dir) / "uploads"


def _load_index() -> list[dict]:
    index_path = _uploads_dir() / ASSET_INDEX_FILE
    if index_path.exists():
        return json.loads(index_path.read_text(encoding="utf-8"))
    return []


def _save_index(assets: list[dict]):
    index_path = _uploads_dir() / ASSET_INDEX_FILE
    index_path.write_text(json.dumps(assets, ensure_ascii=False, indent=2), encoding="utf-8")


@router.post("/upload", response_model=AssetResponse)
async def upload_asset(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed")

    content = await file.read()
    max_bytes = config.storage.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail="File too large")

    asset_id = str(uuid.uuid4())
    safe_name = f"{asset_id}{ext}"
    dest = _uploads_dir() / safe_name
    dest.write_bytes(content)

    asset_entry = {
        "asset_id": asset_id,
        "filename": file.filename or "unknown",
        "stored_name": safe_name,
        "content_type": file.content_type or "application/octet-stream",
        "size": len(content),
    }
    assets = _load_index()
    assets.append(asset_entry)
    _save_index(assets)

    return AssetResponse(**asset_entry)


@router.get("", response_model=list[AssetResponse])
async def list_assets():
    return [AssetResponse(**a) for a in _load_index()]


@router.delete("/{asset_id}")
async def delete_asset(asset_id: str):
    assets = _load_index()
    target = None
    for a in assets:
        if a["asset_id"] == asset_id:
            target = a
            break
    if target is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    file_path = _uploads_dir() / target["stored_name"]
    if file_path.exists():
        file_path.unlink()

    assets = [a for a in assets if a["asset_id"] != asset_id]
    _save_index(assets)

    return {"status": "deleted"}
