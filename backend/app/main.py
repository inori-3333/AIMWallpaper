from contextlib import asynccontextmanager
from fastapi import FastAPI
from pathlib import Path

from app.config import config
from app.api.assets import router as assets_router
from app.api.project import router as project_router
from app.api.knowledge import router as knowledge_router
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure data directories exist
    data_dir = Path(config.storage.data_dir)
    for sub in ["uploads", "projects", "examples"]:
        (data_dir / sub).mkdir(parents=True, exist_ok=True)
    init_db()
    yield


app = FastAPI(title="AIMWallpaper", version="0.1.0", lifespan=lifespan)

app.include_router(assets_router)
app.include_router(project_router)
app.include_router(knowledge_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
