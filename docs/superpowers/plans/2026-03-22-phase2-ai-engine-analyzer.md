# Phase 2: AI Engine, Example Analyzer & Vector Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add LLM integration (LiteLLM), example analyzer for parsing WE project files, ChromaDB vector search for semantic pattern retrieval, and the example import/scan API endpoints.

**Architecture:** AI engine provides a unified interface over multiple LLM providers via LiteLLM. Example analyzer parses WE project folders (scene.json) to extract effect patterns. ChromaDB stores embeddings alongside SQLite for hybrid retrieval. Config model is extended with AI/embedding settings.

**Tech Stack:** LiteLLM, ChromaDB, sentence-transformers (local embedding fallback), litellm embedding API

**Spec:** `docs/superpowers/specs/2026-03-22-aimwallpaper-design.md` (Sections 3, 4.2, 7.3)

**Depends on:** Phase 1 (complete) — FastAPI app, Pydantic models, SQLAlchemy ORM, KnowledgeBaseService

---

## File Structure

```
backend/
├── app/
│   ├── config.py                      ← Modify: add AI and embedding config models
│   ├── core/
│   │   ├── ai_engine.py               ← Create: LiteLLM unified LLM interface
│   │   ├── embedding.py               ← Create: embedding generation (LiteLLM / local)
│   │   ├── vector_store.py            ← Create: ChromaDB wrapper for semantic search
│   │   ├── example_analyzer.py        ← Create: parse WE project folders
│   │   └── knowledge_base.py          ← Modify: add semantic search method
│   ├── api/
│   │   ├── examples.py                ← Create: example import/scan/list endpoints
│   │   └── knowledge.py               ← Modify: add questions endpoints
│   └── main.py                        ← Modify: register examples router
├── tests/
│   ├── test_ai_engine.py              ← Create: AI engine tests
│   ├── test_embedding.py              ← Create: embedding tests
│   ├── test_vector_store.py           ← Create: ChromaDB tests
│   ├── test_example_analyzer.py       ← Create: analyzer tests
│   ├── test_api_examples.py           ← Create: examples API tests
│   └── fixtures/                      ← Create: test WE project fixtures
│       └── sample_project/
│           ├── project.json
│           └── scene.json
└── pyproject.toml                     ← Modify: add new dependencies
```

---

## Task 1: Add Dependencies & Extend Config

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/config.py`
- Test: `backend/tests/test_config.py`

- [ ] **Step 1: Write config tests**

```python
# backend/tests/test_config.py
from app.config import AppConfig, AIProviderConfig, EmbeddingConfig


class TestConfigModels:
    def test_ai_config_defaults(self):
        cfg = AppConfig()
        assert cfg.ai.default_provider == "openai"
        assert cfg.ai.openai.model == "gpt-4o"

    def test_embedding_config_defaults(self):
        cfg = AppConfig()
        assert cfg.embedding.provider == "openai"
        assert cfg.embedding.openai_model == "text-embedding-3-small"

    def test_config_from_dict(self):
        data = {
            "ai": {
                "default_provider": "anthropic",
                "anthropic": {"api_key": "sk-test", "model": "claude-sonnet-4-20250514"},
            },
            "embedding": {"provider": "local", "local_model": "all-MiniLM-L6-v2"},
        }
        cfg = AppConfig.model_validate(data)
        assert cfg.ai.default_provider == "anthropic"
        assert cfg.ai.anthropic.api_key == "sk-test"
        assert cfg.embedding.provider == "local"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_config.py -v
```

- [ ] **Step 3: Update pyproject.toml — add new dependencies**

Add to `dependencies` list:
```
"litellm>=1.40.0",
"chromadb>=0.5.0",
```

- [ ] **Step 4: Extend config.py with AI and embedding models**

```python
# backend/app/config.py
from pathlib import Path
from pydantic import BaseModel
import yaml

CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"


class WallpaperEngineConfig(BaseModel):
    path: str = ""
    exe: str = "wallpaper32.exe"


class StorageConfig(BaseModel):
    data_dir: str = "./data"
    max_upload_size_mb: int = 500
    preview_timeout_seconds: int = 10


class LLMProviderConfig(BaseModel):
    api_key: str = ""
    model: str = ""
    base_url: str = ""


class AIProviderConfig(BaseModel):
    default_provider: str = "openai"
    openai: LLMProviderConfig = LLMProviderConfig(model="gpt-4o")
    anthropic: LLMProviderConfig = LLMProviderConfig(model="claude-sonnet-4-20250514")
    ollama: LLMProviderConfig = LLMProviderConfig(
        base_url="http://localhost:11434", model="llama3"
    )


class EmbeddingConfig(BaseModel):
    provider: str = "openai"
    openai_model: str = "text-embedding-3-small"
    local_model: str = "all-MiniLM-L6-v2"


class AppConfig(BaseModel):
    wallpaper_engine: WallpaperEngineConfig = WallpaperEngineConfig()
    storage: StorageConfig = StorageConfig()
    ai: AIProviderConfig = AIProviderConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()


def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        return AppConfig.model_validate(raw)
    return AppConfig()


config = load_config()
```

- [ ] **Step 5: Install new deps and run tests**

```bash
cd backend && pip install -e ".[dev]" && python -m pytest tests/test_config.py tests/test_models.py -v
```

- [ ] **Step 6: Commit**

```bash
git add backend/pyproject.toml backend/app/config.py backend/tests/test_config.py
git commit -m "feat: extend config with AI provider and embedding settings, add litellm and chromadb deps"
```

---

## Task 2: AI Engine (LiteLLM Wrapper)

**Files:**
- Create: `backend/app/core/ai_engine.py`
- Test: `backend/tests/test_ai_engine.py`

Unified interface for calling LLMs. Uses LiteLLM under the hood. Supports chat completion with system prompt and conversation history.

- [ ] **Step 1: Write tests**

```python
# backend/tests/test_ai_engine.py
import pytest
from unittest.mock import patch, MagicMock
from app.core.ai_engine import AIEngine


class TestAIEngine:
    def test_build_model_string_openai(self):
        engine = AIEngine(provider="openai", model="gpt-4o", api_key="sk-test")
        assert engine._model_string() == "gpt-4o"

    def test_build_model_string_anthropic(self):
        engine = AIEngine(provider="anthropic", model="claude-sonnet-4-20250514", api_key="sk-test")
        assert engine._model_string() == "claude-sonnet-4-20250514"

    def test_build_model_string_ollama(self):
        engine = AIEngine(provider="ollama", model="llama3", base_url="http://localhost:11434")
        assert engine._model_string() == "ollama/llama3"

    @patch("app.core.ai_engine.litellm_completion")
    def test_chat_completion(self, mock_completion):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! I can help with wallpapers."
        mock_completion.return_value = mock_response

        engine = AIEngine(provider="openai", model="gpt-4o", api_key="sk-test")
        result = engine.chat(
            system_prompt="You are a wallpaper assistant.",
            messages=[{"role": "user", "content": "Hi"}],
        )
        assert result == "Hello! I can help with wallpapers."
        mock_completion.assert_called_once()

    @patch("app.core.ai_engine.litellm_completion")
    def test_chat_with_retries_on_timeout(self, mock_completion):
        mock_completion.side_effect = [
            Exception("timeout"),
            MagicMock(choices=[MagicMock(message=MagicMock(content="OK"))]),
        ]
        engine = AIEngine(provider="openai", model="gpt-4o", api_key="sk-test")
        result = engine.chat(
            system_prompt="test",
            messages=[{"role": "user", "content": "test"}],
        )
        assert result == "OK"
        assert mock_completion.call_count == 2

    @patch("app.core.ai_engine.litellm_completion")
    def test_chat_max_retries_exceeded(self, mock_completion):
        mock_completion.side_effect = Exception("timeout")
        engine = AIEngine(provider="openai", model="gpt-4o", api_key="sk-test")
        with pytest.raises(Exception, match="timeout"):
            engine.chat(
                system_prompt="test",
                messages=[{"role": "user", "content": "test"}],
            )
        assert mock_completion.call_count == 3

    def test_from_config(self):
        from app.config import AppConfig
        cfg = AppConfig()
        engine = AIEngine.from_config(cfg)
        assert engine.provider == "openai"
        assert engine.model == "gpt-4o"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_ai_engine.py -v
```

- [ ] **Step 3: Implement ai_engine.py**

```python
# backend/app/core/ai_engine.py
import time
from litellm import completion as litellm_completion
from app.config import AppConfig


class AIEngine:
    def __init__(
        self,
        provider: str,
        model: str,
        api_key: str = "",
        base_url: str = "",
        max_retries: int = 3,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.max_retries = max_retries

    def _model_string(self) -> str:
        if self.provider == "ollama":
            return f"ollama/{self.model}"
        return self.model

    def chat(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float = 0.7,
    ) -> str:
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        kwargs = {
            "model": self._model_string(),
            "messages": full_messages,
            "temperature": temperature,
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["api_base"] = self.base_url

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = litellm_completion(**kwargs)
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(1 * (attempt + 1))  # simple backoff
        raise last_error

    @classmethod
    def from_config(cls, cfg: AppConfig) -> "AIEngine":
        provider = cfg.ai.default_provider
        provider_cfg = getattr(cfg.ai, provider)
        return cls(
            provider=provider,
            model=provider_cfg.model,
            api_key=provider_cfg.api_key,
            base_url=provider_cfg.base_url,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_ai_engine.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/ai_engine.py backend/tests/test_ai_engine.py
git commit -m "feat: add AI engine with LiteLLM wrapper, retry logic, and multi-provider support"
```

---

## Task 3: Embedding Service

**Files:**
- Create: `backend/app/core/embedding.py`
- Test: `backend/tests/test_embedding.py`

Generates text embeddings via LiteLLM's embedding API. Used by vector store to index and query effect patterns.

- [ ] **Step 1: Write tests**

```python
# backend/tests/test_embedding.py
import pytest
from unittest.mock import patch, MagicMock
from app.core.embedding import EmbeddingService


class TestEmbeddingService:
    @patch("app.core.embedding.litellm_embedding")
    def test_embed_text(self, mock_embed):
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_embed.return_value = mock_response

        svc = EmbeddingService(provider="openai", model="text-embedding-3-small", api_key="sk-test")
        result = svc.embed("rain effect")
        assert result == [0.1, 0.2, 0.3]
        mock_embed.assert_called_once()

    @patch("app.core.embedding.litellm_embedding")
    def test_embed_batch(self, mock_embed):
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1, 0.2]),
            MagicMock(embedding=[0.3, 0.4]),
        ]
        mock_embed.return_value = mock_response

        svc = EmbeddingService(provider="openai", model="text-embedding-3-small", api_key="sk-test")
        result = svc.embed_batch(["rain", "snow"])
        assert len(result) == 2

    def test_from_config(self):
        from app.config import AppConfig
        cfg = AppConfig()
        svc = EmbeddingService.from_config(cfg)
        assert svc.model == "text-embedding-3-small"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_embedding.py -v
```

- [ ] **Step 3: Implement embedding.py**

```python
# backend/app/core/embedding.py
from litellm import embedding as litellm_embedding
from app.config import AppConfig


class EmbeddingService:
    def __init__(self, provider: str, model: str, api_key: str = ""):
        self.provider = provider
        self.model = model
        self.api_key = api_key

    def _model_string(self) -> str:
        return self.model

    def embed(self, text: str) -> list[float]:
        kwargs = {"model": self._model_string(), "input": [text]}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        response = litellm_embedding(**kwargs)
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        kwargs = {"model": self._model_string(), "input": texts}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        response = litellm_embedding(**kwargs)
        return [item.embedding for item in response.data]

    @classmethod
    def from_config(cls, cfg: AppConfig) -> "EmbeddingService":
        provider = cfg.embedding.provider
        if provider == "openai":
            model = cfg.embedding.openai_model
        else:
            model = cfg.embedding.local_model
        api_key = cfg.ai.openai.api_key if provider == "openai" else ""
        return cls(provider=provider, model=model, api_key=api_key)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_embedding.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/embedding.py backend/tests/test_embedding.py
git commit -m "feat: add embedding service with LiteLLM for text-to-vector conversion"
```

---

## Task 4: Vector Store (ChromaDB Wrapper)

**Files:**
- Create: `backend/app/core/vector_store.py`
- Test: `backend/tests/test_vector_store.py`

Wraps ChromaDB to store and query effect pattern embeddings. Provides add/query/delete operations.

- [ ] **Step 1: Write tests**

```python
# backend/tests/test_vector_store.py
import pytest
from app.core.vector_store import VectorStore


@pytest.fixture
def vector_store(tmp_path):
    return VectorStore(persist_dir=str(tmp_path / "chroma"))


class TestVectorStore:
    def test_add_and_query(self, vector_store):
        vector_store.add(
            doc_id="pattern_1",
            text="rain drops falling from sky",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"category": "weather", "confidence": 0.85},
        )
        results = vector_store.query(
            query_embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            n_results=5,
        )
        assert len(results) >= 1
        assert results[0]["id"] == "pattern_1"

    def test_add_multiple_and_query(self, vector_store):
        vector_store.add("p1", "rain effect", [0.1, 0.2, 0.3, 0.0, 0.0], {"category": "weather"})
        vector_store.add("p2", "snow effect", [0.0, 0.2, 0.3, 0.1, 0.0], {"category": "weather"})
        vector_store.add("p3", "fire effect", [0.9, 0.0, 0.0, 0.1, 0.0], {"category": "particle"})

        results = vector_store.query([0.1, 0.2, 0.3, 0.0, 0.0], n_results=2)
        assert len(results) == 2
        # rain should be closest
        assert results[0]["id"] == "p1"

    def test_delete(self, vector_store):
        vector_store.add("p1", "rain", [0.1, 0.2, 0.3, 0.0, 0.0], {})
        vector_store.delete("p1")
        results = vector_store.query([0.1, 0.2, 0.3, 0.0, 0.0], n_results=5)
        assert len(results) == 0

    def test_query_empty_store(self, vector_store):
        results = vector_store.query([0.1, 0.2, 0.3], n_results=5)
        assert results == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_vector_store.py -v
```

- [ ] **Step 3: Implement vector_store.py**

```python
# backend/app/core/vector_store.py
import chromadb
from pathlib import Path


class VectorStore:
    def __init__(self, persist_dir: str = "./data/chroma", collection_name: str = "effect_patterns"):
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(
        self,
        doc_id: str,
        text: str,
        embedding: list[float],
        metadata: dict | None = None,
    ):
        self._collection.upsert(
            ids=[doc_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata or {}],
        )

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        where: dict | None = None,
    ) -> list[dict]:
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where

        try:
            results = self._collection.query(**kwargs)
        except Exception:
            return []

        if not results["ids"] or not results["ids"][0]:
            return []

        output = []
        for i, doc_id in enumerate(results["ids"][0]):
            output.append({
                "id": doc_id,
                "document": results["documents"][0][i] if results["documents"] else "",
                "distance": results["distances"][0][i] if results["distances"] else 0,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            })
        return output

    def delete(self, doc_id: str):
        try:
            self._collection.delete(ids=[doc_id])
        except Exception:
            pass

    def count(self) -> int:
        return self._collection.count()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_vector_store.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/vector_store.py backend/tests/test_vector_store.py
git commit -m "feat: add ChromaDB vector store wrapper for semantic pattern search"
```

---

## Task 5: Example Analyzer

**Files:**
- Create: `backend/app/core/example_analyzer.py`
- Create: `backend/tests/fixtures/sample_project/project.json`
- Create: `backend/tests/fixtures/sample_project/scene.json`
- Test: `backend/tests/test_example_analyzer.py`

Parses WE project folders to extract structure: objects, effects, materials, scripts. Does NOT do AI analysis — just raw parsing.

- [ ] **Step 1: Create test fixtures**

```json
// backend/tests/fixtures/sample_project/project.json
{
  "title": "Night City Rain",
  "type": "scene",
  "file": "scene.json",
  "tags": ["cityscape", "rain", "night"]
}
```

```json
// backend/tests/fixtures/sample_project/scene.json
{
  "camera": {"center": [0, 0, 0], "eye": [0, 0, 1]},
  "general": {
    "properties": {
      "schemecolor": {"value": "0.2 0.1 0.3"}
    }
  },
  "objects": [
    {
      "name": "background",
      "image": "materials/bg.png",
      "visible": true,
      "origin": "960 540 0",
      "scale": "1 1 1",
      "effects": [
        {
          "name": "rain",
          "file": "effects/rain.json",
          "passes": [
            {
              "combos": {"RAIN": 1},
              "textures": ["materials/raindrop.png"]
            }
          ]
        }
      ]
    },
    {
      "name": "clock_layer",
      "image": "",
      "visible": true,
      "effects": []
    }
  ]
}
```

- [ ] **Step 2: Write tests**

```python
# backend/tests/test_example_analyzer.py
import pytest
from pathlib import Path
from app.core.example_analyzer import ExampleAnalyzer

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sample_project"


class TestExampleAnalyzer:
    def test_parse_project_folder(self):
        analyzer = ExampleAnalyzer()
        result = analyzer.parse(FIXTURES_DIR)
        assert result["title"] == "Night City Rain"
        assert result["type"] == "scene"

    def test_extract_objects(self):
        analyzer = ExampleAnalyzer()
        result = analyzer.parse(FIXTURES_DIR)
        assert len(result["objects"]) == 2
        assert result["objects"][0]["name"] == "background"

    def test_extract_effects(self):
        analyzer = ExampleAnalyzer()
        result = analyzer.parse(FIXTURES_DIR)
        bg = result["objects"][0]
        assert len(bg["effects"]) == 1
        assert bg["effects"][0]["name"] == "rain"

    def test_extract_effect_details(self):
        analyzer = ExampleAnalyzer()
        result = analyzer.parse(FIXTURES_DIR)
        rain = result["objects"][0]["effects"][0]
        assert rain["passes"][0]["combos"] == {"RAIN": 1}
        assert "raindrop.png" in rain["passes"][0]["textures"][0]

    def test_summary(self):
        analyzer = ExampleAnalyzer()
        result = analyzer.parse(FIXTURES_DIR)
        summary = analyzer.summarize(result)
        assert "background" in summary
        assert "rain" in summary

    def test_parse_nonexistent_folder(self):
        analyzer = ExampleAnalyzer()
        with pytest.raises(FileNotFoundError):
            analyzer.parse(Path("/nonexistent/path"))

    def test_parse_missing_scene_json(self, tmp_path):
        # project.json exists but scene.json doesn't
        (tmp_path / "project.json").write_text('{"title": "test", "type": "scene", "file": "scene.json"}')
        analyzer = ExampleAnalyzer()
        with pytest.raises(FileNotFoundError, match="scene.json"):
            analyzer.parse(tmp_path)
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_example_analyzer.py -v
```

- [ ] **Step 4: Implement example_analyzer.py**

```python
# backend/app/core/example_analyzer.py
import json
from pathlib import Path


class ExampleAnalyzer:
    """Parses Wallpaper Engine project folders to extract structure."""

    def parse(self, project_path: Path) -> dict:
        project_path = Path(project_path)
        if not project_path.exists():
            raise FileNotFoundError(f"Project path not found: {project_path}")

        # Read project.json
        project_file = project_path / "project.json"
        if project_file.exists():
            project_data = json.loads(project_file.read_text(encoding="utf-8"))
        else:
            project_data = {}

        # Read scene.json
        scene_file_name = project_data.get("file", "scene.json")
        scene_file = project_path / scene_file_name
        if not scene_file.exists():
            raise FileNotFoundError(f"scene.json not found at: {scene_file}")

        scene_data = json.loads(scene_file.read_text(encoding="utf-8"))

        return {
            "title": project_data.get("title", ""),
            "type": project_data.get("type", "scene"),
            "tags": project_data.get("tags", []),
            "path": str(project_path),
            "camera": scene_data.get("camera", {}),
            "general": scene_data.get("general", {}),
            "objects": scene_data.get("objects", []),
        }

    def summarize(self, parsed: dict) -> str:
        """Generate a text summary for embedding/display."""
        parts = [f"Title: {parsed.get('title', 'Untitled')}"]
        tags = parsed.get("tags", [])
        if tags:
            parts.append(f"Tags: {', '.join(tags)}")

        for obj in parsed.get("objects", []):
            obj_desc = f"Layer '{obj.get('name', 'unnamed')}'"
            effects = obj.get("effects", [])
            if effects:
                effect_names = [e.get("name", "unnamed") for e in effects]
                obj_desc += f" with effects: {', '.join(effect_names)}"
            parts.append(obj_desc)

        return ". ".join(parts)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_example_analyzer.py -v
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/example_analyzer.py backend/tests/test_example_analyzer.py backend/tests/fixtures/
git commit -m "feat: add example analyzer for parsing WE project folders"
```

---

## Task 6: Semantic Search in Knowledge Base

**Files:**
- Modify: `backend/app/core/knowledge_base.py`
- Test: `backend/tests/test_knowledge_base.py` (add new tests)

Add `semantic_search` method to KnowledgeBaseService that uses VectorStore + EmbeddingService for similarity search, falling back to text search when embeddings are unavailable.

- [ ] **Step 1: Write new tests**

Add to `backend/tests/test_knowledge_base.py`:

```python
from unittest.mock import MagicMock
from app.core.vector_store import VectorStore


class TestSemanticSearch:
    def test_semantic_search_with_vector_store(self, db_session, tmp_path):
        vs = VectorStore(persist_dir=str(tmp_path / "chroma"))
        mock_embedding_svc = MagicMock()
        mock_embedding_svc.embed.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]

        kb = KnowledgeBaseService(db_session, vector_store=vs, embedding_svc=mock_embedding_svc)

        # Create pattern — should also add to vector store
        p = kb.create_pattern(
            name="Rain Effect",
            description="Falling rain drops from the sky",
            category="weather",
        )

        results = kb.semantic_search("rain falling from sky", limit=5)
        assert len(results) >= 1
        assert results[0].name == "Rain Effect"

    def test_semantic_search_fallback_to_text(self, db_session):
        """When no vector store, falls back to text search."""
        kb = KnowledgeBaseService(db_session)
        kb.create_pattern(name="Rain Effect", description="Rain", category="weather")
        results = kb.semantic_search("rain", limit=5)
        assert len(results) >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_knowledge_base.py::TestSemanticSearch -v
```

- [ ] **Step 3: Modify knowledge_base.py**

```python
# backend/app/core/knowledge_base.py
import json
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.db.models import EffectPattern


class KnowledgeBaseService:
    def __init__(self, session: Session, vector_store=None, embedding_svc=None):
        self.session = session
        self.vector_store = vector_store
        self.embedding_svc = embedding_svc

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

        # Index in vector store if available
        if self.vector_store and self.embedding_svc:
            text = f"{name}. {description}"
            embedding = self.embedding_svc.embed(text)
            self.vector_store.add(
                doc_id=str(pattern.id),
                text=text,
                embedding=embedding,
                metadata={"category": category, "confidence": confidence},
            )

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
            if self.vector_store:
                self.vector_store.delete(str(pattern_id))

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

    def semantic_search(self, query: str, limit: int = 5) -> list[EffectPattern]:
        """Semantic search using vector store, falls back to text search."""
        if self.vector_store and self.embedding_svc:
            query_embedding = self.embedding_svc.embed(query)
            results = self.vector_store.query(query_embedding, n_results=limit)
            if results:
                pattern_ids = [int(r["id"]) for r in results]
                stmt = select(EffectPattern).where(EffectPattern.id.in_(pattern_ids))
                return list(self.session.execute(stmt).scalars().all())
        # Fallback to text search
        return self.search_patterns(query)[:limit]
```

- [ ] **Step 4: Run ALL knowledge base tests**

```bash
cd backend && python -m pytest tests/test_knowledge_base.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/knowledge_base.py backend/tests/test_knowledge_base.py
git commit -m "feat: add semantic search to knowledge base with ChromaDB vector store"
```

---

## Task 7: Examples API Endpoints

**Files:**
- Create: `backend/app/api/examples.py`
- Modify: `backend/app/main.py` (register router)
- Test: `backend/tests/test_api_examples.py`

REST endpoints for importing examples (from folder path), listing imported examples, and scanning WE workshop directory.

- [ ] **Step 1: Write tests**

```python
# backend/tests/test_api_examples.py
import pytest
import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sample_project"


class TestExamplesAPI:
    def test_import_example_from_path(self, client, tmp_data_dir):
        resp = client.post(
            "/api/examples/import",
            json={"path": str(FIXTURES_DIR)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Night City Rain"
        assert data["object_count"] == 2

    def test_import_nonexistent_path(self, client, tmp_data_dir):
        resp = client.post(
            "/api/examples/import",
            json={"path": "/nonexistent/path"},
        )
        assert resp.status_code == 400

    def test_list_examples(self, client, tmp_data_dir):
        # Import one first
        client.post("/api/examples/import", json={"path": str(FIXTURES_DIR)})
        resp = client.get("/api/examples")
        assert resp.status_code == 200
        examples = resp.json()
        assert len(examples) >= 1
        assert examples[0]["title"] == "Night City Rain"

    def test_scan_nonexistent_directory(self, client, tmp_data_dir):
        resp = client.post("/api/examples/scan", json={"path": "/nonexistent/workshop"})
        assert resp.status_code == 400

    def test_scan_empty_directory(self, client, tmp_data_dir):
        scan_dir = tmp_data_dir / "workshop"
        scan_dir.mkdir()
        resp = client.post("/api/examples/scan", json={"path": str(scan_dir)})
        assert resp.status_code == 200
        assert resp.json()["imported_count"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_api_examples.py -v
```

- [ ] **Step 3: Implement api/examples.py**

```python
# backend/app/api/examples.py
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
    # Avoid duplicates by path
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
                continue  # skip broken projects

    # Merge into index
    examples = _load_index()
    existing_paths = {e.get("path") for e in examples}
    for entry in imported:
        if entry["path"] not in existing_paths:
            examples.append(entry)

    _save_index(examples)

    return {"imported_count": len(imported), "total_count": len(examples)}
```

- [ ] **Step 4: Register router in main.py**

```python
from app.api.examples import router as examples_router
app.include_router(examples_router)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_api_examples.py -v
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/examples.py backend/app/main.py backend/tests/test_api_examples.py
git commit -m "feat: add examples import, list, and scan API endpoints"
```

---

## Task 8: Full Phase 2 Integration Test

**Files:**
- Modify: `backend/tests/test_integration.py`

- [ ] **Step 1: Add Phase 2 integration tests**

Append to `backend/tests/test_integration.py`:

```python
from pathlib import Path
from unittest.mock import patch, MagicMock

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sample_project"


def test_example_import_and_list(client, tmp_data_dir):
    """Import an example project and verify it appears in listing."""
    resp = client.post("/api/examples/import", json={"path": str(FIXTURES_DIR)})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Night City Rain"

    resp = client.get("/api/examples")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@patch("app.core.ai_engine.litellm_completion")
def test_ai_engine_from_config(mock_completion, client):
    """Verify AI engine can be instantiated from config."""
    from app.core.ai_engine import AIEngine
    from app.config import config as app_config
    engine = AIEngine.from_config(app_config)
    assert engine.provider == app_config.ai.default_provider
```

- [ ] **Step 2: Run ALL tests**

```bash
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_integration.py
git commit -m "feat: add Phase 2 integration tests for examples and AI engine"
```

---

## Summary

After completing all 8 tasks, you will have:

- **AI Engine** — LiteLLM wrapper with retry logic, multi-provider support (OpenAI/Anthropic/Ollama)
- **Embedding Service** — text-to-vector conversion via LiteLLM embedding API
- **Vector Store** — ChromaDB wrapper for semantic similarity search
- **Example Analyzer** — parses WE project folders, extracts objects/effects/structure
- **Semantic Search** — KnowledgeBaseService upgraded with vector-based search + text fallback
- **Examples API** — import from folder path, list, batch scan workshop directory
- **Extended Config** — AI provider and embedding model configuration

**Next phases:**
- Phase 3: Scene Builder + Project Generator + SceneScript + Preview
- Phase 4: WebSocket Chat + React Frontend
