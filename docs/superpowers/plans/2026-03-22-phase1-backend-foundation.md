# Phase 1: Backend Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the backend foundation — project scaffolding, Pydantic data models, SQLite database, knowledge base CRUD, asset management, and basic REST API endpoints — producing a testable FastAPI server.

**Architecture:** Bottom-up build: data models first, then database layer, then service logic, then API endpoints. Each layer tested independently before moving up. Single-user local app, no auth needed.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 + SQLite, pytest, uvicorn, aiofiles, Pillow, python-multipart

**Spec:** `docs/superpowers/specs/2026-03-22-aimwallpaper-design.md`

---

## File Structure

```
AIMWallpaper/
├── backend/
│   ├── pyproject.toml              ← Project metadata + dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 ← FastAPI app entry point
│   │   ├── config.py               ← Settings from config.yaml
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── scene.py            ← WE scene.json Pydantic schema
│   │   │   ├── project.py          ← WE project.json Pydantic schema
│   │   │   ├── effect.py           ← Effect-related Pydantic models
│   │   │   └── api.py              ← API request/response models
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py         ← SQLite engine + session factory
│   │   │   └── models.py           ← SQLAlchemy ORM models
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── knowledge_base.py   ← Knowledge base CRUD service
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── assets.py           ← Asset upload/list/delete endpoints
│   │       ├── project.py          ← Project CRUD endpoints
│   │       └── knowledge.py        ← Knowledge base endpoints
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py             ← Shared fixtures (test DB, client)
│       ├── test_models.py          ← Pydantic model tests
│       ├── test_database.py        ← DB layer tests
│       ├── test_knowledge_base.py  ← Knowledge base service tests
│       ├── test_api_assets.py      ← Asset API tests
│       ├── test_api_projects.py    ← Project API tests
│       └── test_api_knowledge.py   ← Knowledge API tests
├── data/                           ← Runtime data (gitignored)
└── config.yaml                     ← Global config file
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `config.yaml`
- Create: `.gitignore`

- [ ] **Step 1: Create pyproject.toml with dependencies**

```toml
[project]
name = "aimwallpaper-backend"
version = "0.1.0"
description = "AI-driven Wallpaper Engine wallpaper creation tool"
requires-python = ">=3.11"
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
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 2: Create config.yaml with default settings**

```yaml
wallpaper_engine:
  path: "E:\\SteamLibrary\\steamapps\\common\\wallpaper_engine"
  exe: "wallpaper32.exe"

ai:
  default_provider: "openai"
  openai:
    api_key: ""
    model: "gpt-4o"
  anthropic:
    api_key: ""
    model: "claude-sonnet-4-20250514"
  ollama:
    base_url: "http://localhost:11434"
    model: "llama3"

embedding:
  provider: "openai"
  openai:
    model: "text-embedding-3-small"
  local:
    model: "all-MiniLM-L6-v2"

storage:
  data_dir: "./data"
  max_upload_size_mb: 500
  preview_timeout_seconds: 10
```

- [ ] **Step 3: Create app/config.py — loads config.yaml into a Pydantic Settings model**

```python
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import yaml

CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"


class WallpaperEngineConfig(BaseModel):
    path: str = ""
    exe: str = "wallpaper32.exe"


class StorageConfig(BaseModel):
    data_dir: str = "./data"
    max_upload_size_mb: int = 500
    preview_timeout_seconds: int = 10


class AppConfig(BaseModel):
    wallpaper_engine: WallpaperEngineConfig = WallpaperEngineConfig()
    storage: StorageConfig = StorageConfig()


def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        return AppConfig.model_validate(raw)
    return AppConfig()


config = load_config()
```

- [ ] **Step 4: Create app/main.py — minimal FastAPI app**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure data directories exist
    data_dir = Path(config.storage.data_dir)
    for sub in ["uploads", "projects", "examples"]:
        (data_dir / sub).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="AIMWallpaper", version="0.1.0", lifespan=lifespan)


@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Create empty __init__.py files**

Create empty `__init__.py` in: `backend/app/`, `backend/app/models/`, `backend/app/db/`, `backend/app/core/`, `backend/app/api/`, `backend/tests/`

- [ ] **Step 6: Create .gitignore**

```gitignore
__pycache__/
*.pyc
*.egg-info/
.venv/
data/
*.db
node_modules/
dist/
.env
```

- [ ] **Step 7: Install dependencies and verify server starts**

```bash
cd backend
pip install -e ".[dev]"
cd ..
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 &
sleep 3
curl http://127.0.0.1:8000/api/health
# Expected: {"status":"ok"}
# Then kill the server
```

- [ ] **Step 8: Commit**

```bash
git add backend/pyproject.toml backend/app/ backend/tests/__init__.py config.yaml .gitignore
git commit -m "feat: scaffold backend project with FastAPI, config, and health endpoint"
```

---

## Task 2: Pydantic Data Models for WE Schemas

**Files:**
- Create: `backend/app/models/scene.py`
- Create: `backend/app/models/project.py`
- Create: `backend/app/models/effect.py`
- Create: `backend/app/models/api.py`
- Create: `backend/app/models/__init__.py` (update)
- Test: `backend/tests/test_models.py`

These models represent WE's scene.json and project.json structures. They're used for validation when generating wallpaper project files.

- [ ] **Step 1: Write tests for Pydantic models**

```python
# backend/tests/test_models.py
import pytest
from app.models.scene import SceneObject, SceneEffect, Scene
from app.models.project import WEProject
from app.models.effect import EffectPass
from app.models.api import AssetResponse, ProjectResponse


class TestSceneModels:
    def test_scene_object_minimal(self):
        obj = SceneObject(name="bg", image="materials/bg.png")
        assert obj.name == "bg"
        assert obj.visible is True  # default
        assert obj.effects == []

    def test_scene_object_with_effects(self):
        effect = SceneEffect(
            name="rain",
            file="effects/rain.json",
            passes=[EffectPass(combos={"RAIN": 1}, textures=[])]
        )
        obj = SceneObject(name="bg", image="materials/bg.png", effects=[effect])
        assert len(obj.effects) == 1
        assert obj.effects[0].name == "rain"

    def test_scene_roundtrip(self):
        """Scene can be serialized to JSON and parsed back."""
        scene = Scene(
            camera={"center": [0, 0, 0], "eye": [0, 0, 1]},
            general={"properties": {"schemecolor": {"value": "0 0 0"}}},
            objects=[
                SceneObject(name="bg", image="materials/bg.png", origin="0 0 0", scale="1 1 1")
            ],
        )
        data = scene.model_dump()
        parsed = Scene.model_validate(data)
        assert parsed.objects[0].name == "bg"

    def test_scene_empty_objects_allowed(self):
        scene = Scene()
        assert scene.objects == []


class TestProjectModel:
    def test_project_minimal(self):
        proj = WEProject(
            title="My Wallpaper",
            type="web",
            file="scene.json",
        )
        assert proj.title == "My Wallpaper"

    def test_project_with_tags(self):
        proj = WEProject(
            title="Night City",
            type="scene",
            file="scene.json",
            tags=["cityscape", "night"],
        )
        assert "night" in proj.tags


class TestApiModels:
    def test_asset_response(self):
        resp = AssetResponse(
            asset_id="abc-123",
            filename="bg.png",
            content_type="image/png",
            size=1024,
        )
        assert resp.asset_id == "abc-123"

    def test_project_response(self):
        resp = ProjectResponse(
            project_id="p-1",
            name="Test",
            created_at="2026-01-01T00:00:00",
        )
        assert resp.project_id == "p-1"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_models.py -v
# Expected: FAIL — ImportError (modules don't exist yet)
```

- [ ] **Step 3: Implement effect.py**

```python
# backend/app/models/effect.py
from pydantic import BaseModel


class EffectPass(BaseModel):
    combos: dict = {}
    textures: list[str] = []
    constantshadervalues: dict = {}
    model_config = {"extra": "allow"}
```

- [ ] **Step 4: Implement scene.py**

```python
# backend/app/models/scene.py
from pydantic import BaseModel
from app.models.effect import EffectPass


class SceneEffect(BaseModel):
    name: str = ""
    file: str = ""
    passes: list[EffectPass] = []
    model_config = {"extra": "allow"}


class SceneObject(BaseModel):
    name: str = ""
    image: str = ""
    visible: bool = True
    origin: str = "0 0 0"
    scale: str = "1 1 1"
    angles: str = "0 0 0"
    effects: list[SceneEffect] = []
    model_config = {"extra": "allow"}


class Scene(BaseModel):
    camera: dict = {}
    general: dict = {}
    objects: list[SceneObject] = []
    model_config = {"extra": "allow"}
```

- [ ] **Step 5: Implement project.py**

```python
# backend/app/models/project.py
from pydantic import BaseModel


class WEProject(BaseModel):
    title: str
    type: str = "scene"
    file: str = "scene.json"
    description: str = ""
    tags: list[str] = []
    visibility: str = "private"
    model_config = {"extra": "allow"}
```

- [ ] **Step 6: Implement api.py**

```python
# backend/app/models/api.py
from pydantic import BaseModel


class AssetResponse(BaseModel):
    asset_id: str
    filename: str
    content_type: str
    size: int


class ProjectCreate(BaseModel):
    name: str
    description: str = ""


class ProjectResponse(BaseModel):
    project_id: str
    name: str
    description: str = ""
    created_at: str
    version: int = 1


class ErrorResponse(BaseModel):
    detail: str
```

- [ ] **Step 7: Update models/__init__.py**

```python
# backend/app/models/__init__.py
from app.models.scene import Scene, SceneObject, SceneEffect
from app.models.project import WEProject
from app.models.effect import EffectPass
from app.models.api import AssetResponse, ProjectCreate, ProjectResponse
```

- [ ] **Step 8: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_models.py -v
# Expected: all PASS
```

- [ ] **Step 9: Commit**

```bash
git add backend/app/models/ backend/tests/test_models.py
git commit -m "feat: add Pydantic data models for WE scene, project, and API schemas"
```

---

## Task 3: Database Layer (SQLAlchemy + SQLite)

**Files:**
- Create: `backend/app/db/database.py`
- Create: `backend/app/db/models.py`
- Create: `backend/app/db/__init__.py` (update)
- Test: `backend/tests/test_database.py`
- Test: `backend/tests/conftest.py`

ORM models for knowledge base tables: effect_patterns, field_knowledge, composition_rules, script_snippets. Plus a projects table to track wallpaper projects.

- [ ] **Step 1: Write tests for database layer**

```python
# backend/tests/test_database.py
import pytest
from sqlalchemy import select
from app.db.models import EffectPattern, FieldKnowledge, CompositionRule, ScriptSnippet, Project


class TestEffectPattern:
    def test_create_pattern(self, db_session):
        pattern = EffectPattern(
            name="Rain",
            description="Falling rain drops",
            category="weather",
            tags="rain,weather,particles",
            confidence=0.85,
            source="example_001",
            verified=False,
            components='{"type": "particle", "rate": 200}',
            params='{"rate": {"min": 50, "max": 500, "default": 200}}',
        )
        db_session.add(pattern)
        db_session.commit()

        result = db_session.execute(select(EffectPattern).where(EffectPattern.name == "Rain")).scalar_one()
        assert result.confidence == 0.85
        assert result.category == "weather"

    def test_pattern_defaults(self, db_session):
        pattern = EffectPattern(name="Test", description="test")
        db_session.add(pattern)
        db_session.commit()
        assert pattern.confidence == 0.5
        assert pattern.verified is False


class TestFieldKnowledge:
    def test_create_field(self, db_session):
        field = FieldKnowledge(
            path="objects[].effects[].passes[].combos",
            description="Shader combo flags",
            value_type="dict",
            examples='{"RAIN": 1}',
            confidence=0.9,
        )
        db_session.add(field)
        db_session.commit()
        assert field.id is not None


class TestCompositionRule:
    def test_create_rule(self, db_session):
        rule = CompositionRule(
            rule="Rain and snow effects should not be combined on the same layer",
            source="example_002",
            verified=True,
        )
        db_session.add(rule)
        db_session.commit()
        assert rule.verified is True


class TestScriptSnippet:
    def test_create_snippet(self, db_session):
        snippet = ScriptSnippet(
            name="clock_update",
            description="Updates a clock display every second",
            code='export function update(value) { /* ... */ }',
            api_used="thisLayer,engine.registerUpdate",
            tags="clock,time,component",
        )
        db_session.add(snippet)
        db_session.commit()
        assert snippet.name == "clock_update"


class TestProject:
    def test_create_project(self, db_session):
        proj = Project(name="Night City", description="Cyberpunk cityscape wallpaper")
        db_session.add(proj)
        db_session.commit()
        assert proj.id is not None
        assert proj.version == 1

    def test_project_timestamps(self, db_session):
        proj = Project(name="Test")
        db_session.add(proj)
        db_session.commit()
        assert proj.created_at is not None
        assert proj.updated_at is not None
```

- [ ] **Step 2: Write conftest.py with test DB fixture**

```python
# backend/tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.database import Base

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_database.py -v
# Expected: FAIL — ImportError
```

- [ ] **Step 4: Implement db/database.py**

```python
# backend/app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session
from pathlib import Path
from app.config import config


class Base(DeclarativeBase):
    pass


def get_engine(db_path: str | None = None):
    if db_path is None:
        data_dir = Path(config.storage.data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path = str(data_dir / "knowledge.db")
    return create_engine(f"sqlite:///{db_path}", echo=False)


def get_session(engine=None) -> Session:
    if engine is None:
        engine = get_engine()
    return Session(engine)


def init_db(engine=None):
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)
```

- [ ] **Step 5: Implement db/models.py**

```python
# backend/app/db/models.py
from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class EffectPattern(Base):
    __tablename__ = "effect_patterns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(100), default="")
    tags: Mapped[str] = mapped_column(Text, default="")  # comma-separated
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    source: Mapped[str] = mapped_column(String(200), default="")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    components: Mapped[str] = mapped_column(Text, default="{}")  # JSON string
    params: Mapped[str] = mapped_column(Text, default="{}")  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class FieldKnowledge(Base):
    __tablename__ = "field_knowledge"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    value_type: Mapped[str] = mapped_column(String(50), default="")
    examples: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    user_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class CompositionRule(Base):
    __tablename__ = "composition_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(200), default="")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    user_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ScriptSnippet(Base):
    __tablename__ = "script_snippets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    code: Mapped[str] = mapped_column(Text, default="")
    api_used: Mapped[str] = mapped_column(Text, default="")  # comma-separated
    tags: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    scene_json: Mapped[str] = mapped_column(Text, default="{}")
    project_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
```

- [ ] **Step 6: Update db/__init__.py**

```python
# backend/app/db/__init__.py
from app.db.database import Base, get_engine, get_session, init_db
from app.db.models import EffectPattern, FieldKnowledge, CompositionRule, ScriptSnippet, Project
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_database.py -v
# Expected: all PASS
```

- [ ] **Step 8: Commit**

```bash
git add backend/app/db/ backend/tests/conftest.py backend/tests/test_database.py
git commit -m "feat: add SQLAlchemy ORM models and database layer for knowledge base"
```

---

## Task 4: Knowledge Base CRUD Service

**Files:**
- Create: `backend/app/core/knowledge_base.py`
- Test: `backend/tests/test_knowledge_base.py`

Service layer that provides create, read, update, delete, and query operations on the knowledge base tables.

- [ ] **Step 1: Write tests for knowledge base service**

```python
# backend/tests/test_knowledge_base.py
import pytest
from app.core.knowledge_base import KnowledgeBaseService
from app.db.models import EffectPattern


class TestPatternCRUD:
    def test_create_pattern(self, db_session):
        kb = KnowledgeBaseService(db_session)
        pattern = kb.create_pattern(
            name="Rain",
            description="Rain drops falling",
            category="weather",
            tags=["rain", "weather"],
            confidence=0.85,
            components={"type": "particle"},
            params={"rate": {"min": 50, "max": 500}},
        )
        assert pattern.id is not None
        assert pattern.name == "Rain"

    def test_get_pattern(self, db_session):
        kb = KnowledgeBaseService(db_session)
        created = kb.create_pattern(name="Snow", description="Snowfall", category="weather")
        fetched = kb.get_pattern(created.id)
        assert fetched is not None
        assert fetched.name == "Snow"

    def test_get_pattern_not_found(self, db_session):
        kb = KnowledgeBaseService(db_session)
        assert kb.get_pattern(999) is None

    def test_list_patterns(self, db_session):
        kb = KnowledgeBaseService(db_session)
        kb.create_pattern(name="Rain", description="Rain", category="weather")
        kb.create_pattern(name="Fire", description="Fire", category="particle")
        patterns = kb.list_patterns()
        assert len(patterns) == 2

    def test_list_patterns_by_category(self, db_session):
        kb = KnowledgeBaseService(db_session)
        kb.create_pattern(name="Rain", description="Rain", category="weather")
        kb.create_pattern(name="Fire", description="Fire", category="particle")
        patterns = kb.list_patterns(category="weather")
        assert len(patterns) == 1
        assert patterns[0].name == "Rain"

    def test_verify_pattern(self, db_session):
        kb = KnowledgeBaseService(db_session)
        p = kb.create_pattern(name="Rain", description="Rain", confidence=0.6)
        updated = kb.verify_pattern(p.id)
        assert updated.verified is True
        assert updated.confidence >= 0.9

    def test_delete_pattern(self, db_session):
        kb = KnowledgeBaseService(db_session)
        p = kb.create_pattern(name="Rain", description="Rain")
        kb.delete_pattern(p.id)
        assert kb.get_pattern(p.id) is None

    def test_update_confidence(self, db_session):
        kb = KnowledgeBaseService(db_session)
        p = kb.create_pattern(name="Rain", description="Rain", confidence=0.5)
        updated = kb.update_confidence(p.id, delta=0.1)
        assert updated.confidence == pytest.approx(0.6)

    def test_confidence_clamped(self, db_session):
        kb = KnowledgeBaseService(db_session)
        p = kb.create_pattern(name="Rain", description="Rain", confidence=0.95)
        updated = kb.update_confidence(p.id, delta=0.2)
        assert updated.confidence == 1.0

        updated2 = kb.update_confidence(p.id, delta=-2.0)
        assert updated2.confidence == 0.0


class TestSearchPatterns:
    def test_search_by_name(self, db_session):
        kb = KnowledgeBaseService(db_session)
        kb.create_pattern(name="Rain Effect", description="Falling rain")
        kb.create_pattern(name="Snow Effect", description="Falling snow")
        results = kb.search_patterns("rain")
        assert len(results) == 1
        assert results[0].name == "Rain Effect"

    def test_search_by_tags(self, db_session):
        kb = KnowledgeBaseService(db_session)
        kb.create_pattern(name="Glow", description="Light glow", tags=["light", "glow"])
        kb.create_pattern(name="Rain", description="Rain", tags=["weather"])
        results = kb.search_patterns("glow")
        assert len(results) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_knowledge_base.py -v
# Expected: FAIL — ImportError
```

- [ ] **Step 3: Implement knowledge_base.py**

```python
# backend/app/core/knowledge_base.py
import json
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.db.models import EffectPattern


class KnowledgeBaseService:
    def __init__(self, session: Session):
        self.session = session

    def create_pattern(
        self,
        name: str,
        description: str,
        category: str = "",
        tags: list[str] | None = None,
        confidence: float = 0.5,
        source: str = "",
        components: dict | None = None,
        params: dict | None = None,
    ) -> EffectPattern:
        pattern = EffectPattern(
            name=name,
            description=description,
            category=category,
            tags=",".join(tags) if tags else "",
            confidence=confidence,
            source=source,
            components=json.dumps(components or {}),
            params=json.dumps(params or {}),
        )
        self.session.add(pattern)
        self.session.commit()
        self.session.refresh(pattern)
        return pattern

    def get_pattern(self, pattern_id: int) -> EffectPattern | None:
        return self.session.get(EffectPattern, pattern_id)

    def list_patterns(self, category: str | None = None) -> list[EffectPattern]:
        stmt = select(EffectPattern)
        if category:
            stmt = stmt.where(EffectPattern.category == category)
        return list(self.session.execute(stmt).scalars().all())

    def verify_pattern(self, pattern_id: int) -> EffectPattern:
        pattern = self.session.get(EffectPattern, pattern_id)
        if pattern is None:
            raise ValueError(f"Pattern {pattern_id} not found")
        pattern.verified = True
        pattern.confidence = max(pattern.confidence, 0.9)
        self.session.commit()
        self.session.refresh(pattern)
        return pattern

    def delete_pattern(self, pattern_id: int) -> None:
        pattern = self.session.get(EffectPattern, pattern_id)
        if pattern:
            self.session.delete(pattern)
            self.session.commit()

    def update_confidence(self, pattern_id: int, delta: float) -> EffectPattern:
        pattern = self.session.get(EffectPattern, pattern_id)
        if pattern is None:
            raise ValueError(f"Pattern {pattern_id} not found")
        pattern.confidence = max(0.0, min(1.0, pattern.confidence + delta))
        self.session.commit()
        self.session.refresh(pattern)
        return pattern

    def search_patterns(self, query: str) -> list[EffectPattern]:
        """Simple text search across name, description, and tags."""
        like_query = f"%{query.lower()}%"
        stmt = select(EffectPattern).where(
            or_(
                EffectPattern.name.ilike(like_query),
                EffectPattern.description.ilike(like_query),
                EffectPattern.tags.ilike(like_query),
            )
        )
        return list(self.session.execute(stmt).scalars().all())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_knowledge_base.py -v
# Expected: all PASS
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/knowledge_base.py backend/tests/test_knowledge_base.py
git commit -m "feat: add knowledge base CRUD service with text search"
```

---

## Task 5: Asset Upload API

**Files:**
- Create: `backend/app/api/assets.py`
- Modify: `backend/app/main.py` (register router)
- Test: `backend/tests/test_api_assets.py`

Handles file upload (multipart/form-data), listing, and deletion. Files stored under `data/uploads/` with UUID-based naming.

- [ ] **Step 1: Write tests for asset API**

```python
# backend/tests/test_api_assets.py
import pytest
from io import BytesIO


class TestAssetUpload:
    def test_upload_image(self, client, tmp_data_dir):
        file_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # fake PNG header
        response = client.post(
            "/api/assets/upload",
            files={"file": ("test.png", BytesIO(file_content), "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "asset_id" in data
        assert data["filename"] == "test.png"
        assert data["content_type"] == "image/png"

    def test_upload_rejected_type(self, client, tmp_data_dir):
        response = client.post(
            "/api/assets/upload",
            files={"file": ("hack.exe", BytesIO(b"malicious"), "application/octet-stream")},
        )
        assert response.status_code == 400

    def test_list_assets(self, client, tmp_data_dir):
        # Upload two files
        for name in ["a.png", "b.jpg"]:
            client.post(
                "/api/assets/upload",
                files={"file": (name, BytesIO(b"\x89PNG" + b"\x00" * 50), "image/png")},
            )
        response = client.get("/api/assets")
        assert response.status_code == 200
        assets = response.json()
        assert len(assets) >= 2

    def test_delete_asset(self, client, tmp_data_dir):
        resp = client.post(
            "/api/assets/upload",
            files={"file": ("del.png", BytesIO(b"\x89PNG" + b"\x00" * 50), "image/png")},
        )
        asset_id = resp.json()["asset_id"]
        del_resp = client.delete(f"/api/assets/{asset_id}")
        assert del_resp.status_code == 200

        # Verify gone from listing
        list_resp = client.get("/api/assets")
        ids = [a["asset_id"] for a in list_resp.json()]
        assert asset_id not in ids

    def test_delete_nonexistent(self, client, tmp_data_dir):
        resp = client.delete("/api/assets/nonexistent-id")
        assert resp.status_code == 404
```

- [ ] **Step 2: Update conftest.py with client and tmp_data_dir fixtures**

```python
# backend/tests/conftest.py
import pytest
import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from httpx import ASGITransport, AsyncClient
from fastapi.testclient import TestClient

from app.db.database import Base
from app.config import config


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    """Redirect data storage to a temp directory."""
    for sub in ["uploads", "projects", "examples"]:
        (tmp_path / sub).mkdir()
    monkeypatch.setattr(config.storage, "data_dir", str(tmp_path))
    return tmp_path


@pytest.fixture
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_api_assets.py -v
# Expected: FAIL — router not found / 404
```

- [ ] **Step 4: Implement api/assets.py**

```python
# backend/app/api/assets.py
import uuid
import json
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import config
from app.models.api import AssetResponse

router = APIRouter(prefix="/api/assets", tags=["assets"])

ALLOWED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".tga",  # images
    ".mp4", ".webm",  # video
    ".ogg", ".mp3", ".wav",  # audio
    ".pkg", ".json",  # WE project files
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
    # Validate extension
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed")

    # Validate size
    content = await file.read()
    max_bytes = config.storage.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail="File too large")

    # Save with UUID name
    asset_id = str(uuid.uuid4())
    safe_name = f"{asset_id}{ext}"
    dest = _uploads_dir() / safe_name
    dest.write_bytes(content)

    # Update index
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

    # Delete file
    file_path = _uploads_dir() / target["stored_name"]
    if file_path.exists():
        file_path.unlink()

    # Update index
    assets = [a for a in assets if a["asset_id"] != asset_id]
    _save_index(assets)

    return {"status": "deleted"}
```

- [ ] **Step 5: Register router in main.py**

Add to `backend/app/main.py`:
```python
from app.api.assets import router as assets_router

# After app = FastAPI(...)
app.include_router(assets_router)
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_api_assets.py -v
# Expected: all PASS
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/assets.py backend/app/main.py backend/tests/test_api_assets.py backend/tests/conftest.py
git commit -m "feat: add asset upload, list, and delete API endpoints"
```

---

## Task 6: Project CRUD API

**Files:**
- Create: `backend/app/api/project.py`
- Modify: `backend/app/main.py` (register router)
- Modify: `backend/app/main.py` (add DB init to lifespan)
- Modify: `backend/tests/conftest.py` (add db_session override fixture)
- Test: `backend/tests/test_api_projects.py`

REST endpoints for creating, listing, and retrieving wallpaper projects. Projects are stored in SQLite.

- [ ] **Step 1: Write tests for project API**

```python
# backend/tests/test_api_projects.py
import pytest


class TestProjectAPI:
    def test_create_project(self, client, app_db):
        resp = client.post("/api/projects", json={"name": "Night City", "description": "Cyberpunk wallpaper"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Night City"
        assert "project_id" in data

    def test_list_projects(self, client, app_db):
        client.post("/api/projects", json={"name": "Project A"})
        client.post("/api/projects", json={"name": "Project B"})
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_get_project(self, client, app_db):
        create_resp = client.post("/api/projects", json={"name": "Test"})
        pid = create_resp.json()["project_id"]
        resp = client.get(f"/api/projects/{pid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test"

    def test_get_project_not_found(self, client, app_db):
        resp = client.get("/api/projects/999")
        assert resp.status_code == 404

    def test_undo_no_history(self, client, app_db):
        create_resp = client.post("/api/projects", json={"name": "Test"})
        pid = create_resp.json()["project_id"]
        resp = client.post(f"/api/projects/{pid}/undo")
        assert resp.status_code == 400  # nothing to undo
```

- [ ] **Step 2: Update conftest.py with app_db fixture**

Add to `backend/tests/conftest.py`:
```python
from app.db.database import Base, get_engine

@pytest.fixture
def app_db(tmp_path):
    """Create a test DB and patch the app to use it."""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    import app.api.project as proj_module
    original_get_session = proj_module._get_session

    def _test_session():
        return Session(engine)

    proj_module._get_session = _test_session
    yield engine
    proj_module._get_session = original_get_session
    engine.dispose()
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_api_projects.py -v
# Expected: FAIL
```

- [ ] **Step 4: Implement api/project.py**

```python
# backend/app/api/project.py
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_engine
from app.db.models import Project
from app.models.api import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _get_session() -> Session:
    return Session(get_engine())


@router.post("", response_model=ProjectResponse)
def create_project(body: ProjectCreate):
    with _get_session() as session:
        proj = Project(name=body.name, description=body.description)
        session.add(proj)
        session.commit()
        session.refresh(proj)
        return ProjectResponse(
            project_id=str(proj.id),
            name=proj.name,
            description=proj.description,
            created_at=proj.created_at.isoformat(),
            version=proj.version,
        )


@router.get("", response_model=list[ProjectResponse])
def list_projects():
    with _get_session() as session:
        projects = session.query(Project).all()
        return [
            ProjectResponse(
                project_id=str(p.id),
                name=p.name,
                description=p.description,
                created_at=p.created_at.isoformat(),
                version=p.version,
            )
            for p in projects
        ]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str):
    with _get_session() as session:
        proj = session.get(Project, int(project_id))
        if proj is None:
            raise HTTPException(status_code=404, detail="Project not found")
        return ProjectResponse(
            project_id=str(proj.id),
            name=proj.name,
            description=proj.description,
            created_at=proj.created_at.isoformat(),
            version=proj.version,
        )


@router.post("/{project_id}/undo")
def undo_project(project_id: str):
    with _get_session() as session:
        proj = session.get(Project, int(project_id))
        if proj is None:
            raise HTTPException(status_code=404, detail="Project not found")
        if proj.version <= 1:
            raise HTTPException(status_code=400, detail="Nothing to undo")
        # Version snapshot restore will be implemented in Phase 3
        proj.version -= 1
        session.commit()
        return {"status": "ok", "version": proj.version}
```

- [ ] **Step 5: Register router and add DB init in main.py**

```python
# Add to backend/app/main.py
from app.api.project import router as project_router
from app.db.database import init_db

# In lifespan, before yield:
    init_db()

# After app definition:
app.include_router(project_router)
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_api_projects.py -v
# Expected: all PASS
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/project.py backend/app/main.py backend/tests/test_api_projects.py backend/tests/conftest.py
git commit -m "feat: add project CRUD API endpoints with SQLite storage"
```

---

## Task 7: Knowledge Base API

**Files:**
- Create: `backend/app/api/knowledge.py`
- Modify: `backend/app/main.py` (register router)
- Test: `backend/tests/test_api_knowledge.py`

REST endpoints for querying, verifying, and deleting knowledge base patterns.

- [ ] **Step 1: Write tests for knowledge API**

```python
# backend/tests/test_api_knowledge.py
import pytest


class TestKnowledgeAPI:
    def _seed_pattern(self, client):
        """Helper: seed a pattern via internal DB since no create endpoint exists yet."""
        # We'll add a temporary create endpoint for testing, or seed directly
        resp = client.post("/api/knowledge/patterns", json={
            "name": "Rain",
            "description": "Rain effect",
            "category": "weather",
            "tags": ["rain", "weather"],
            "confidence": 0.7,
        })
        return resp.json()

    def test_list_patterns(self, client, knowledge_db):
        self._seed_pattern(client)
        resp = client.get("/api/knowledge/patterns")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_list_patterns_with_search(self, client, knowledge_db):
        self._seed_pattern(client)
        resp = client.get("/api/knowledge/patterns?q=rain")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_verify_pattern(self, client, knowledge_db):
        data = self._seed_pattern(client)
        pid = data["id"]
        resp = client.put(f"/api/knowledge/patterns/{pid}/verify")
        assert resp.status_code == 200
        assert resp.json()["verified"] is True
        assert resp.json()["confidence"] >= 0.9

    def test_delete_pattern(self, client, knowledge_db):
        data = self._seed_pattern(client)
        pid = data["id"]
        resp = client.delete(f"/api/knowledge/patterns/{pid}")
        assert resp.status_code == 200

        list_resp = client.get("/api/knowledge/patterns")
        ids = [p["id"] for p in list_resp.json()]
        assert pid not in ids

    def test_delete_nonexistent(self, client, knowledge_db):
        resp = client.delete("/api/knowledge/patterns/9999")
        assert resp.status_code == 404
```

- [ ] **Step 2: Add knowledge_db fixture to conftest.py**

Add to `backend/tests/conftest.py`:
```python
@pytest.fixture
def knowledge_db(tmp_path):
    """Create a test DB and patch knowledge API to use it."""
    db_path = tmp_path / "test_kb.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    import app.api.knowledge as kb_module
    original = kb_module._get_session

    def _test_session():
        return Session(engine)

    kb_module._get_session = _test_session
    yield engine
    kb_module._get_session = original
    engine.dispose()
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_api_knowledge.py -v
# Expected: FAIL
```

- [ ] **Step 4: Implement api/knowledge.py**

```python
# backend/app/api/knowledge.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_engine
from app.core.knowledge_base import KnowledgeBaseService

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class PatternCreate(BaseModel):
    name: str
    description: str = ""
    category: str = ""
    tags: list[str] = []
    confidence: float = 0.5
    source: str = ""


class PatternOut(BaseModel):
    id: int
    name: str
    description: str
    category: str
    tags: str
    confidence: float
    verified: bool


def _get_session() -> Session:
    return Session(get_engine())


@router.post("/patterns", response_model=PatternOut)
def create_pattern(body: PatternCreate):
    with _get_session() as session:
        kb = KnowledgeBaseService(session)
        p = kb.create_pattern(
            name=body.name,
            description=body.description,
            category=body.category,
            tags=body.tags,
            confidence=body.confidence,
            source=body.source,
        )
        return PatternOut(
            id=p.id, name=p.name, description=p.description,
            category=p.category, tags=p.tags, confidence=p.confidence, verified=p.verified,
        )


@router.get("/patterns", response_model=list[PatternOut])
def list_patterns(q: str | None = None, category: str | None = None):
    with _get_session() as session:
        kb = KnowledgeBaseService(session)
        if q:
            patterns = kb.search_patterns(q)
        else:
            patterns = kb.list_patterns(category=category)
        return [
            PatternOut(
                id=p.id, name=p.name, description=p.description,
                category=p.category, tags=p.tags, confidence=p.confidence, verified=p.verified,
            )
            for p in patterns
        ]


@router.put("/patterns/{pattern_id}/verify", response_model=PatternOut)
def verify_pattern(pattern_id: int):
    with _get_session() as session:
        kb = KnowledgeBaseService(session)
        try:
            p = kb.verify_pattern(pattern_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Pattern not found")
        return PatternOut(
            id=p.id, name=p.name, description=p.description,
            category=p.category, tags=p.tags, confidence=p.confidence, verified=p.verified,
        )


@router.delete("/patterns/{pattern_id}")
def delete_pattern(pattern_id: int):
    with _get_session() as session:
        kb = KnowledgeBaseService(session)
        if kb.get_pattern(pattern_id) is None:
            raise HTTPException(status_code=404, detail="Pattern not found")
        kb.delete_pattern(pattern_id)
        return {"status": "deleted"}
```

- [ ] **Step 5: Register router in main.py**

```python
from app.api.knowledge import router as knowledge_router
app.include_router(knowledge_router)
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_api_knowledge.py -v
# Expected: all PASS
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/knowledge.py backend/app/main.py backend/tests/test_api_knowledge.py backend/tests/conftest.py
git commit -m "feat: add knowledge base API endpoints for patterns CRUD and search"
```

---

## Task 8: Config API & Full Integration Test

**Files:**
- Modify: `backend/app/main.py` (add config endpoints)
- Test: `backend/tests/test_integration.py`

Add config read/update endpoints. Run a full integration test that exercises the complete API surface.

- [ ] **Step 1: Write integration test**

```python
# backend/tests/test_integration.py
"""Full integration test: exercises the API flow end-to-end."""
from io import BytesIO


def test_full_workflow(client, tmp_data_dir, app_db):
    """Simulate: create project → upload asset → verify health."""
    # 1. Health check
    resp = client.get("/api/health")
    assert resp.status_code == 200

    # 2. Create project
    resp = client.post("/api/projects", json={"name": "Integration Test"})
    assert resp.status_code == 200
    project_id = resp.json()["project_id"]

    # 3. Upload asset
    resp = client.post(
        "/api/assets/upload",
        files={"file": ("bg.png", BytesIO(b"\x89PNG" + b"\x00" * 50), "image/png")},
    )
    assert resp.status_code == 200
    asset_id = resp.json()["asset_id"]

    # 4. List assets
    resp = client.get("/api/assets")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # 5. Get project
    resp = client.get(f"/api/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Integration Test"

    # 6. Get config
    resp = client.get("/api/config")
    assert resp.status_code == 200
    assert "wallpaper_engine" in resp.json()


def test_config_read(client):
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "storage" in data
```

- [ ] **Step 2: Add config endpoints to main.py**

```python
# Add to backend/app/main.py
from app.config import config as app_config

@app.get("/api/config")
def get_config():
    return app_config.model_dump()


@app.put("/api/config")
def update_config(body: dict):
    """Update config values at runtime (non-persistent, in-memory only).
    Persistent config changes require editing config.yaml directly."""
    for key, value in body.items():
        if hasattr(app_config, key):
            sub_model = getattr(app_config, key)
            if isinstance(value, dict) and isinstance(sub_model, BaseModel):
                for k, v in value.items():
                    if hasattr(sub_model, k):
                        setattr(sub_model, k, v)
            else:
                setattr(app_config, key, value)
    return app_config.model_dump()
```

> **Note:** The spec's `GET /api/knowledge/questions` and `POST /api/knowledge/questions/{id}/answer` endpoints are deferred to Phase 2, as they depend on the AI engine which is not yet implemented.

- [ ] **Step 3: Run all tests**

```bash
cd backend && python -m pytest tests/ -v
# Expected: all PASS
```

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_integration.py backend/app/main.py
git commit -m "feat: add config API and full integration test"
```

---

## Summary

After completing all 8 tasks, you will have:

- **Working FastAPI server** with health, config, asset, project, and knowledge base endpoints
- **Pydantic models** for WE scene.json, project.json schemas
- **SQLAlchemy ORM** with all knowledge base tables
- **Knowledge base service** with CRUD + text search
- **Asset management** with upload validation, UUID naming, and type whitelist
- **Test suite** covering models, database, services, API endpoints, and integration

**Next phases:**
- Phase 2: AI Engine + Example Analyzer + ChromaDB vector search
- Phase 3: Scene Builder + Project Generator + SceneScript + Preview
- Phase 4: WebSocket Chat + React Frontend
