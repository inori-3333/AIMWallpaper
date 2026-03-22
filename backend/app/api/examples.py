import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.example_analyzer import ExampleAnalyzer
from app.config import config

router = APIRouter(prefix="/api/examples", tags=["examples"])

EXAMPLES_INDEX = "examples.json"


def _examples_dir() -> Path:
    return Path(config.storage.data_dir) / "examples"


def _load_index() -> list[dict]:
    index_path = _examples_dir() / EXAMPLES_INDEX
    if index_path.exists():
        return json.loads(index_path.read_text(encoding="utf-8"))
    return []


def _save_index(examples: list[dict]):
    index_path = _examples_dir() / EXAMPLES_INDEX
    index_path.write_text(json.dumps(examples, ensure_ascii=False, indent=2), encoding="utf-8")


class ImportRequest(BaseModel):
    path: str


class ScanRequest(BaseModel):
    path: str


@router.post("/import")
def import_example(body: ImportRequest):
    analyzer = ExampleAnalyzer()
    try:
        result = analyzer.parse(Path(body.path))
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    summary = analyzer.summarize(result)
    entry = {
        "title": result["title"],
        "type": result["type"],
        "tags": result["tags"],
        "path": result["path"],
        "object_count": len(result["objects"]),
        "summary": summary,
    }
    examples = _load_index()
    examples = [e for e in examples if e.get("path") != entry["path"]]
    examples.append(entry)
    _save_index(examples)
    return entry


@router.get("")
def list_examples():
    return _load_index()


@router.post("/scan")
def scan_workshop(body: ScanRequest):
    scan_path = Path(body.path)
    if not scan_path.exists():
        raise HTTPException(status_code=400, detail=f"Directory not found: {body.path}")
    analyzer = ExampleAnalyzer()
    imported = []
    for sub in scan_path.iterdir():
        if sub.is_dir() and (sub / "project.json").exists():
            try:
                result = analyzer.parse(sub)
                summary = analyzer.summarize(result)
                imported.append({
                    "title": result["title"],
                    "type": result["type"],
                    "tags": result["tags"],
                    "path": result["path"],
                    "object_count": len(result["objects"]),
                    "summary": summary,
                })
            except Exception:
                continue
    examples = _load_index()
    existing_paths = {e.get("path") for e in examples}
    for entry in imported:
        if entry["path"] not in existing_paths:
            examples.append(entry)
    _save_index(examples)
    return {"imported_count": len(imported), "total_count": len(examples)}
