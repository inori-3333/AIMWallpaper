# Phase 3: Scene Builder, Project Generator, SceneScript & Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add scene.json assembly (SceneBuilder), WE project file generation (ProjectGenerator), SceneScript code generation, WE CLI preview service, and WebSocket chat API for multi-turn AI dialog.

**Architecture:** SceneBuilder assembles scene.json from layers/effects using Pydantic models. ProjectGenerator orchestrates the full pipeline: AI intent parsing → knowledge base lookup → scene building → file output. ScriptGenerator uses the AI engine to produce SceneScript JS code. PreviewService calls WE CLI to render and screenshot. ChatService manages WebSocket sessions with streaming AI responses.

**Tech Stack:** FastAPI WebSocket, existing AIEngine/EmbeddingService/KnowledgeBaseService, Pydantic scene models, subprocess for WE CLI, asyncio

**Spec:** `docs/superpowers/specs/2026-03-22-aimwallpaper-design.md` (Sections 5, 10, 11)

**Depends on:** Phase 1 (FastAPI, models, DB) + Phase 2 (AI engine, knowledge base, vector store, example analyzer)

---

## File Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── scene_builder.py         ← Create: scene.json assembly from layers/effects
│   │   ├── project_generator.py     ← Create: full WE project output pipeline
│   │   ├── script_generator.py      ← Create: SceneScript JS code generation via AI
│   │   └── preview.py               ← Create: WE CLI preview + screenshot capture
│   ├── api/
│   │   ├── chat.py                  ← Create: WebSocket chat endpoint
│   │   └── project.py               ← Modify: add export and preview endpoints
│   ├── models/
│   │   └── chat.py                  ← Create: chat message Pydantic models
│   └── main.py                      ← Modify: register chat router
├── tests/
│   ├── test_scene_builder.py        ← Create
│   ├── test_project_generator.py    ← Create
│   ├── test_script_generator.py     ← Create
│   ├── test_preview.py              ← Create
│   ├── test_api_chat.py             ← Create
│   └── test_integration.py          ← Modify: add Phase 3 integration tests
└── pyproject.toml                   ← Modify: add websockets dependency
```

---

## Task 1: Scene Builder

**Files:**
- Create: `backend/app/core/scene_builder.py`
- Test: `backend/tests/test_scene_builder.py`

SceneBuilder assembles a valid `scene.json` from layers and effects using existing Pydantic models (`Scene`, `SceneObject`, `SceneEffect`).

- [ ] **Step 1: Write tests**

```python
# backend/tests/test_scene_builder.py
import json
import pytest
from app.core.scene_builder import SceneBuilder
from app.models.scene import Scene, SceneObject, SceneEffect


class TestSceneBuilder:
    def test_create_empty_scene(self):
        builder = SceneBuilder()
        scene = builder.build()
        assert isinstance(scene, Scene)
        assert scene.objects == []

    def test_add_image_layer(self):
        builder = SceneBuilder()
        builder.add_layer(name="background", image="materials/bg.png")
        scene = builder.build()
        assert len(scene.objects) == 1
        assert scene.objects[0].name == "background"
        assert scene.objects[0].image == "materials/bg.png"

    def test_add_effect_to_layer(self):
        builder = SceneBuilder()
        builder.add_layer(name="bg", image="materials/bg.png")
        builder.add_effect("bg", name="rain", file="effects/rain.json",
                           passes=[{"combos": {"RAIN": 1}, "textures": ["materials/raindrop.png"]}])
        scene = builder.build()
        assert len(scene.objects[0].effects) == 1
        assert scene.objects[0].effects[0].name == "rain"

    def test_add_effect_to_nonexistent_layer_raises(self):
        builder = SceneBuilder()
        with pytest.raises(ValueError, match="not found"):
            builder.add_effect("missing", name="rain")

    def test_set_camera(self):
        builder = SceneBuilder()
        builder.set_camera(center=[0, 0, 0], eye=[0, 0, 1])
        scene = builder.build()
        assert scene.camera["center"] == [0, 0, 0]

    def test_set_general_properties(self):
        builder = SceneBuilder()
        builder.set_general({"properties": {"schemecolor": {"value": "0.2 0.1 0.3"}}})
        scene = builder.build()
        assert "schemecolor" in scene.general["properties"]

    def test_to_json(self):
        builder = SceneBuilder()
        builder.add_layer(name="bg", image="bg.png")
        result = builder.to_json()
        parsed = json.loads(result)
        assert "objects" in parsed
        assert parsed["objects"][0]["name"] == "bg"

    def test_from_scene(self):
        """Load an existing scene for modification."""
        original = Scene(
            camera={"center": [0, 0, 0]},
            objects=[SceneObject(name="bg", image="bg.png")]
        )
        builder = SceneBuilder.from_scene(original)
        builder.add_layer(name="overlay", image="overlay.png")
        scene = builder.build()
        assert len(scene.objects) == 2

    def test_remove_layer(self):
        builder = SceneBuilder()
        builder.add_layer(name="bg", image="bg.png")
        builder.add_layer(name="overlay", image="overlay.png")
        builder.remove_layer("bg")
        scene = builder.build()
        assert len(scene.objects) == 1
        assert scene.objects[0].name == "overlay"

    def test_remove_effect(self):
        builder = SceneBuilder()
        builder.add_layer(name="bg", image="bg.png")
        builder.add_effect("bg", name="rain")
        builder.add_effect("bg", name="blur")
        builder.remove_effect("bg", "rain")
        scene = builder.build()
        assert len(scene.objects[0].effects) == 1
        assert scene.objects[0].effects[0].name == "blur"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_scene_builder.py -v
```

- [ ] **Step 3: Implement scene_builder.py**

```python
# backend/app/core/scene_builder.py
import json
from app.models.scene import Scene, SceneObject, SceneEffect
from app.models.effect import EffectPass


class SceneBuilder:
    def __init__(self):
        self._camera: dict = {}
        self._general: dict = {}
        self._objects: list[SceneObject] = []

    @classmethod
    def from_scene(cls, scene: Scene) -> "SceneBuilder":
        builder = cls()
        builder._camera = scene.camera.copy() if scene.camera else {}
        builder._general = scene.general.copy() if scene.general else {}
        builder._objects = list(scene.objects)
        return builder

    def set_camera(self, center: list | None = None, eye: list | None = None):
        if center is not None:
            self._camera["center"] = center
        if eye is not None:
            self._camera["eye"] = eye

    def set_general(self, general: dict):
        self._general = general

    def add_layer(self, name: str, image: str = "", visible: bool = True,
                  origin: str = "0 0 0", scale: str = "1 1 1", **kwargs) -> SceneObject:
        obj = SceneObject(name=name, image=image, visible=visible,
                          origin=origin, scale=scale, **kwargs)
        self._objects.append(obj)
        return obj

    def remove_layer(self, name: str):
        self._objects = [o for o in self._objects if o.name != name]

    def _find_layer(self, name: str) -> SceneObject:
        for obj in self._objects:
            if obj.name == name:
                return obj
        raise ValueError(f"Layer '{name}' not found")

    def add_effect(self, layer_name: str, name: str = "", file: str = "",
                   passes: list[dict] | None = None) -> SceneEffect:
        layer = self._find_layer(layer_name)
        effect_passes = [EffectPass(**p) for p in (passes or [])]
        effect = SceneEffect(name=name, file=file, passes=effect_passes)
        layer.effects.append(effect)
        return effect

    def remove_effect(self, layer_name: str, effect_name: str):
        layer = self._find_layer(layer_name)
        layer.effects = [e for e in layer.effects if e.name != effect_name]

    def build(self) -> Scene:
        return Scene(camera=self._camera, general=self._general, objects=self._objects)

    def to_json(self, indent: int = 2) -> str:
        scene = self.build()
        return json.dumps(scene.model_dump(), indent=indent, ensure_ascii=False)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_scene_builder.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/scene_builder.py backend/tests/test_scene_builder.py
git commit -m "feat: add SceneBuilder for assembling WE scene.json from layers and effects"
```

---

## Task 2: Project Generator

**Files:**
- Create: `backend/app/core/project_generator.py`
- Test: `backend/tests/test_project_generator.py`

ProjectGenerator takes a project DB record, builds scene.json + project.json, writes them to disk as a complete WE project folder. Also handles version snapshots.

- [ ] **Step 1: Write tests**

```python
# backend/tests/test_project_generator.py
import json
import pytest
from pathlib import Path
from app.core.project_generator import ProjectGenerator
from app.core.scene_builder import SceneBuilder


class TestProjectGenerator:
    def test_generate_project_folder(self, tmp_path):
        gen = ProjectGenerator(output_dir=str(tmp_path))
        builder = SceneBuilder()
        builder.add_layer(name="bg", image="materials/bg.png")

        result = gen.generate(
            project_id="1",
            title="My Wallpaper",
            scene_builder=builder,
            tags=["night", "rain"],
        )

        project_dir = tmp_path / "1"
        assert project_dir.exists()
        assert (project_dir / "project.json").exists()
        assert (project_dir / "scene.json").exists()

    def test_project_json_content(self, tmp_path):
        gen = ProjectGenerator(output_dir=str(tmp_path))
        builder = SceneBuilder()
        builder.add_layer(name="bg", image="bg.png")

        gen.generate(project_id="1", title="Test", scene_builder=builder)
        project_data = json.loads((tmp_path / "1" / "project.json").read_text())
        assert project_data["title"] == "Test"
        assert project_data["type"] == "scene"
        assert project_data["file"] == "scene.json"

    def test_scene_json_content(self, tmp_path):
        gen = ProjectGenerator(output_dir=str(tmp_path))
        builder = SceneBuilder()
        builder.add_layer(name="bg", image="bg.png")

        gen.generate(project_id="1", title="Test", scene_builder=builder)
        scene_data = json.loads((tmp_path / "1" / "scene.json").read_text())
        assert len(scene_data["objects"]) == 1

    def test_version_snapshot(self, tmp_path):
        gen = ProjectGenerator(output_dir=str(tmp_path))
        builder1 = SceneBuilder()
        builder1.add_layer(name="bg", image="bg.png")
        gen.generate(project_id="1", title="Test", scene_builder=builder1, version=1)

        builder2 = SceneBuilder()
        builder2.add_layer(name="bg", image="bg.png")
        builder2.add_layer(name="overlay", image="overlay.png")
        gen.generate(project_id="1", title="Test", scene_builder=builder2, version=2)

        # Both versions should exist
        assert (tmp_path / "1" / "scene.json").exists()
        v1_snapshot = tmp_path / "1" / "snapshots" / "v1"
        assert v1_snapshot.exists()
        assert (v1_snapshot / "scene.json").exists()

    def test_export_to_we_directory(self, tmp_path):
        gen = ProjectGenerator(output_dir=str(tmp_path / "projects"))
        builder = SceneBuilder()
        builder.add_layer(name="bg", image="bg.png")
        gen.generate(project_id="1", title="Test", scene_builder=builder)

        we_dir = tmp_path / "we_projects"
        we_dir.mkdir()
        gen.export(project_id="1", target_dir=str(we_dir / "MyWallpaper"))

        assert (we_dir / "MyWallpaper" / "project.json").exists()
        assert (we_dir / "MyWallpaper" / "scene.json").exists()

    def test_copy_assets(self, tmp_path):
        """Assets referenced in scene should be copied to project folder."""
        # Create a fake asset
        uploads = tmp_path / "uploads"
        uploads.mkdir()
        (uploads / "bg.png").write_bytes(b"\x89PNG" + b"\x00" * 10)

        gen = ProjectGenerator(output_dir=str(tmp_path / "projects"), assets_dir=str(uploads))
        builder = SceneBuilder()
        builder.add_layer(name="bg", image="bg.png")
        gen.generate(project_id="1", title="Test", scene_builder=builder)

        assert (tmp_path / "projects" / "1" / "materials" / "bg.png").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_project_generator.py -v
```

- [ ] **Step 3: Implement project_generator.py**

```python
# backend/app/core/project_generator.py
import json
import shutil
from pathlib import Path
from app.core.scene_builder import SceneBuilder
from app.models.project import WEProject


class ProjectGenerator:
    def __init__(self, output_dir: str = "./data/projects", assets_dir: str = "./data/uploads"):
        self.output_dir = Path(output_dir)
        self.assets_dir = Path(assets_dir)

    def generate(
        self,
        project_id: str,
        title: str,
        scene_builder: SceneBuilder,
        tags: list[str] | None = None,
        version: int = 1,
    ) -> Path:
        project_dir = self.output_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        # Snapshot previous version if exists
        if version > 1:
            self._snapshot(project_dir, version - 1)

        # Write project.json
        project_data = WEProject(title=title, tags=tags or [])
        (project_dir / "project.json").write_text(
            json.dumps(project_data.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Write scene.json
        scene_json = scene_builder.to_json()
        (project_dir / "scene.json").write_text(scene_json, encoding="utf-8")

        # Copy referenced assets
        scene = scene_builder.build()
        self._copy_assets(scene, project_dir)

        return project_dir

    def _snapshot(self, project_dir: Path, prev_version: int):
        snapshot_dir = project_dir / "snapshots" / f"v{prev_version}"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        for f in ["scene.json", "project.json"]:
            src = project_dir / f
            if src.exists():
                shutil.copy2(src, snapshot_dir / f)

    def _copy_assets(self, scene, project_dir: Path):
        materials_dir = project_dir / "materials"
        for obj in scene.objects:
            if obj.image:
                src = self.assets_dir / obj.image
                if src.exists():
                    materials_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, materials_dir / Path(obj.image).name)

    def export(self, project_id: str, target_dir: str):
        src = self.output_dir / project_id
        if not src.exists():
            raise FileNotFoundError(f"Project {project_id} not found at {src}")
        target = Path(target_dir)
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(src, target, dirs_exist_ok=True)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_project_generator.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/project_generator.py backend/tests/test_project_generator.py
git commit -m "feat: add ProjectGenerator for WE project file output with versioning and export"
```

---

## Task 3: SceneScript Generator

**Files:**
- Create: `backend/app/core/script_generator.py`
- Test: `backend/tests/test_script_generator.py`

Uses AIEngine to generate SceneScript (JavaScript) code for custom effects. Includes basic JS syntax validation.

- [ ] **Step 1: Write tests**

```python
# backend/tests/test_script_generator.py
import pytest
from unittest.mock import MagicMock
from app.core.script_generator import ScriptGenerator


class TestScriptGenerator:
    def test_generate_script(self):
        mock_engine = MagicMock()
        mock_engine.chat.return_value = '''export function update(value) {
    thisLayer.opacity = Math.sin(engine.runtime * 2) * 0.5 + 0.5;
}'''
        gen = ScriptGenerator(ai_engine=mock_engine)
        result = gen.generate("Make the layer pulse in opacity")
        assert "update" in result
        assert "thisLayer" in result

    def test_generate_with_context(self):
        mock_engine = MagicMock()
        mock_engine.chat.return_value = 'export function update() { thisLayer.x = input.cursorWorldPosition.x; }'
        gen = ScriptGenerator(ai_engine=mock_engine)
        result = gen.generate("Follow mouse cursor", context={"layer_name": "particle", "api_hints": ["input.cursorWorldPosition"]})
        assert "cursorWorldPosition" in result
        mock_engine.chat.assert_called_once()
        call_args = mock_engine.chat.call_args
        assert "cursorWorldPosition" in str(call_args)

    def test_validate_syntax_valid(self):
        gen = ScriptGenerator(ai_engine=MagicMock())
        code = 'export function update() { return 1; }'
        assert gen.validate_syntax(code) is True

    def test_validate_syntax_invalid(self):
        gen = ScriptGenerator(ai_engine=MagicMock())
        code = 'function { broken syntax ((('
        assert gen.validate_syntax(code) is False

    def test_validate_api_whitelist(self):
        gen = ScriptGenerator(ai_engine=MagicMock())
        safe_code = 'thisLayer.opacity = 1; engine.runtime; input.cursorWorldPosition;'
        assert gen.check_api_usage(safe_code) == []

    def test_validate_api_blacklist(self):
        gen = ScriptGenerator(ai_engine=MagicMock())
        unsafe_code = 'fetch("http://evil.com"); eval("code");'
        violations = gen.check_api_usage(unsafe_code)
        assert "fetch" in violations
        assert "eval" in violations

    def test_generate_with_retry_on_invalid(self):
        mock_engine = MagicMock()
        mock_engine.chat.side_effect = [
            'function { broken',  # invalid first attempt
            'export function update() { thisLayer.opacity = 1; }',  # valid retry
        ]
        gen = ScriptGenerator(ai_engine=mock_engine)
        result = gen.generate("Set opacity to 1")
        assert "update" in result
        assert mock_engine.chat.call_count == 2
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_script_generator.py -v
```

- [ ] **Step 3: Implement script_generator.py**

```python
# backend/app/core/script_generator.py
import ast
import re


SCENESCRIPT_SYSTEM_PROMPT = """You are a Wallpaper Engine SceneScript code generator.
SceneScript is an ECMAScript 2018 subset for WE wallpapers.

Core APIs available:
- thisScene: access scene properties
- thisLayer: access current layer (opacity, x, y, scale, angles, color)
- input: user input (cursorWorldPosition, cursorScreenPosition, audioLevel)
- engine: runtime info (engine.runtime = elapsed seconds, engine.frametime = delta)

Rules:
- Export functions: export function init(), export function update(value)
- No DOM, no fetch, no eval, no require/import from external modules
- Keep code minimal and focused on the requested effect
- Use only known SceneScript APIs

Return ONLY the JavaScript code, no markdown fences or explanation."""

BLOCKED_APIS = ["fetch", "eval", "XMLHttpRequest", "require", "import(", "Function(", "setTimeout", "setInterval"]


class ScriptGenerator:
    def __init__(self, ai_engine, max_retries: int = 3):
        self.ai_engine = ai_engine
        self.max_retries = max_retries

    def generate(self, description: str, context: dict | None = None) -> str:
        ctx = context or {}
        user_msg = f"Generate SceneScript for: {description}"
        if ctx.get("layer_name"):
            user_msg += f"\nTarget layer: {ctx['layer_name']}"
        if ctx.get("api_hints"):
            user_msg += f"\nRelevant APIs: {', '.join(ctx['api_hints'])}"

        for attempt in range(self.max_retries):
            code = self.ai_engine.chat(
                system_prompt=SCENESCRIPT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
                temperature=0.3,
            )
            # Strip markdown fences if present
            code = self._strip_fences(code)

            if self.validate_syntax(code):
                violations = self.check_api_usage(code)
                if not violations:
                    return code
                user_msg = f"Previous code used blocked APIs: {violations}. Fix and regenerate for: {description}"
            else:
                user_msg = f"Previous code had syntax errors. Fix and regenerate for: {description}"

        return code  # return last attempt even if imperfect

    def validate_syntax(self, code: str) -> bool:
        # Strip ES module syntax that Python's ast can't parse
        cleaned = re.sub(r'\bexport\s+', '', code)
        try:
            # Use a simple heuristic: check balanced braces and basic structure
            brace_count = 0
            for ch in cleaned:
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                if brace_count < 0:
                    return False
            return brace_count == 0 and ('function' in cleaned or '=>' in cleaned or '=' in cleaned)
        except Exception:
            return False

    def check_api_usage(self, code: str) -> list[str]:
        violations = []
        for api in BLOCKED_APIS:
            if api in code:
                violations.append(api.rstrip("("))
        return violations

    def _strip_fences(self, code: str) -> str:
        code = code.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            lines = lines[1:]  # remove opening fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)
        return code.strip()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_script_generator.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/script_generator.py backend/tests/test_script_generator.py
git commit -m "feat: add SceneScript generator with AI-powered code gen and validation"
```

---

## Task 4: Preview Service

**Files:**
- Create: `backend/app/core/preview.py`
- Test: `backend/tests/test_preview.py`

Calls WE CLI to load a wallpaper, captures a screenshot. Degrades gracefully when WE is not installed.

- [ ] **Step 1: Write tests**

```python
# backend/tests/test_preview.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
from app.core.preview import PreviewService


class TestPreviewService:
    def test_build_command(self):
        svc = PreviewService(we_path="/steam/wallpaper_engine", we_exe="wallpaper32.exe")
        cmd = svc._build_command("/projects/1/project.json")
        assert "wallpaper32.exe" in cmd[0] or "wallpaper32.exe" in str(cmd)
        assert "openWallpaper" in cmd

    def test_we_not_installed(self):
        svc = PreviewService(we_path="/nonexistent/path")
        assert svc.is_available() is False

    def test_we_installed(self, tmp_path):
        exe = tmp_path / "wallpaper32.exe"
        exe.write_bytes(b"fake")
        svc = PreviewService(we_path=str(tmp_path))
        assert svc.is_available() is True

    @patch("app.core.preview.subprocess")
    def test_capture_preview(self, mock_subprocess, tmp_path):
        exe = tmp_path / "wallpaper32.exe"
        exe.write_bytes(b"fake")
        mock_subprocess.run.return_value = MagicMock(returncode=0)

        svc = PreviewService(we_path=str(tmp_path), screenshot_dir=str(tmp_path / "screenshots"))

        # Mock screenshot capture (since we can't actually run WE in tests)
        screenshot_path = tmp_path / "screenshots" / "1_preview.png"
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        screenshot_path.write_bytes(b"\x89PNG" + b"\x00" * 10)

        with patch.object(svc, "_capture_screenshot", return_value=str(screenshot_path)):
            result = svc.preview(project_path=str(tmp_path / "project.json"), project_id="1")
            assert result is not None
            assert "1_preview.png" in result

    def test_preview_unavailable_returns_none(self):
        svc = PreviewService(we_path="/nonexistent")
        result = svc.preview(project_path="/some/project.json", project_id="1")
        assert result is None

    def test_from_config(self):
        from app.config import AppConfig
        cfg = AppConfig()
        svc = PreviewService.from_config(cfg)
        assert svc.we_exe == cfg.wallpaper_engine.exe
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_preview.py -v
```

- [ ] **Step 3: Implement preview.py**

```python
# backend/app/core/preview.py
import subprocess
import time
import logging
from pathlib import Path
from app.config import AppConfig

logger = logging.getLogger(__name__)


class PreviewService:
    def __init__(self, we_path: str = "", we_exe: str = "wallpaper32.exe",
                 screenshot_dir: str = "./data/screenshots", timeout: int = 10):
        self.we_path = Path(we_path)
        self.we_exe = we_exe
        self.screenshot_dir = Path(screenshot_dir)
        self.timeout = timeout

    @classmethod
    def from_config(cls, cfg: AppConfig) -> "PreviewService":
        return cls(
            we_path=cfg.wallpaper_engine.path,
            we_exe=cfg.wallpaper_engine.exe,
            timeout=cfg.storage.preview_timeout_seconds,
        )

    def is_available(self) -> bool:
        exe_path = self.we_path / self.we_exe
        return exe_path.exists()

    def _build_command(self, project_json_path: str) -> list[str]:
        exe_path = str(self.we_path / self.we_exe)
        return [
            exe_path, "-control",
            "openWallpaper",
            "-file", project_json_path,
            "-playback", "play",
        ]

    def preview(self, project_path: str, project_id: str) -> str | None:
        if not self.is_available():
            logger.warning("Wallpaper Engine not available at %s", self.we_path)
            return None

        cmd = self._build_command(project_path)
        try:
            subprocess.run(cmd, timeout=self.timeout, check=False)
            time.sleep(3)  # wait for WE to render
            return self._capture_screenshot(project_id)
        except subprocess.TimeoutExpired:
            logger.warning("Preview timed out for project %s", project_id)
            return None
        except Exception as e:
            logger.error("Preview failed: %s", e)
            return None

    def _capture_screenshot(self, project_id: str) -> str:
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = self.screenshot_dir / f"{project_id}_preview.png"
        # Platform-specific screenshot capture
        # On Windows, use mss or similar library
        try:
            import mss
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # primary monitor
                img = sct.grab(monitor)
                from PIL import Image
                pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
                pil_img.save(str(screenshot_path))
        except ImportError:
            logger.warning("mss not installed, cannot capture screenshot")
            return ""
        return str(screenshot_path)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_preview.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/preview.py backend/tests/test_preview.py
git commit -m "feat: add WE CLI preview service with screenshot capture"
```

---

## Task 5: Chat Message Models

**Files:**
- Create: `backend/app/models/chat.py`
- Test: inline with Task 6 tests

Simple Pydantic models for WebSocket chat message types.

- [ ] **Step 1: Create chat models**

```python
# backend/app/models/chat.py
from pydantic import BaseModel


class ChatMessageIn(BaseModel):
    type: str  # "user_message" | "annotation"
    content: str = ""
    region: dict | None = None
    label: str = ""


class ChatMessageOut(BaseModel):
    type: str  # "ai_message" | "ai_thinking" | "generation_start" | "generation_progress" | "generation_complete" | "ai_question" | "error"
    content: str = ""
    task: str = ""
    progress: float = 0.0
    preview_url: str = ""
    question_id: str = ""
    code: str = ""
    message: str = ""
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models/chat.py
git commit -m "feat: add chat message Pydantic models for WebSocket protocol"
```

---

## Task 6: WebSocket Chat API

**Files:**
- Create: `backend/app/api/chat.py`
- Modify: `backend/app/main.py` (register chat router)
- Modify: `backend/pyproject.toml` (add websockets dep)
- Test: `backend/tests/test_api_chat.py`

WebSocket endpoint at `/ws/chat/{project_id}` for multi-turn AI dialog. Uses AIEngine for responses.

- [ ] **Step 1: Write tests**

```python
# backend/tests/test_api_chat.py
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestChatWebSocket:
    @patch("app.api.chat._get_ai_engine")
    def test_websocket_connect_and_send(self, mock_get_engine, client):
        mock_engine = MagicMock()
        mock_engine.chat.return_value = "I can help with that wallpaper!"
        mock_get_engine.return_value = mock_engine

        with client.websocket_connect("/ws/chat/1") as ws:
            ws.send_json({"type": "user_message", "content": "Add rain effect"})
            response = ws.receive_json()
            assert response["type"] in ("ai_thinking", "ai_message")
            # Read all messages until we get ai_message
            messages = [response]
            while response["type"] != "ai_message":
                response = ws.receive_json()
                messages.append(response)
            assert any(m["type"] == "ai_message" for m in messages)

    @patch("app.api.chat._get_ai_engine")
    def test_websocket_conversation_history(self, mock_get_engine, client):
        mock_engine = MagicMock()
        mock_engine.chat.return_value = "Response"
        mock_get_engine.return_value = mock_engine

        with client.websocket_connect("/ws/chat/1") as ws:
            ws.send_json({"type": "user_message", "content": "Hello"})
            # Drain messages
            while True:
                msg = ws.receive_json()
                if msg["type"] == "ai_message":
                    break

            ws.send_json({"type": "user_message", "content": "Follow up"})
            while True:
                msg = ws.receive_json()
                if msg["type"] == "ai_message":
                    break

            # Verify history was accumulated (2 user messages in second call)
            assert mock_engine.chat.call_count == 2
            second_call = mock_engine.chat.call_args_list[1]
            messages = second_call.kwargs.get("messages") or second_call[1].get("messages") or second_call[0][1]
            assert len(messages) >= 2  # at least 2 user turns

    @patch("app.api.chat._get_ai_engine")
    def test_websocket_error_handling(self, mock_get_engine, client):
        mock_engine = MagicMock()
        mock_engine.chat.side_effect = Exception("LLM timeout")
        mock_get_engine.return_value = mock_engine

        with client.websocket_connect("/ws/chat/1") as ws:
            ws.send_json({"type": "user_message", "content": "test"})
            # Should get thinking then error
            messages = []
            for _ in range(5):
                try:
                    msg = ws.receive_json()
                    messages.append(msg)
                    if msg["type"] == "error":
                        break
                except Exception:
                    break
            assert any(m["type"] == "error" for m in messages)

    @patch("app.api.chat._get_ai_engine")
    def test_websocket_invalid_message(self, mock_get_engine, client):
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        with client.websocket_connect("/ws/chat/1") as ws:
            ws.send_text("not valid json {{{")
            msg = ws.receive_json()
            assert msg["type"] == "error"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_api_chat.py -v
```

- [ ] **Step 3: Add websockets to pyproject.toml**

Add to dependencies:
```
"websockets>=12.0",
```

- [ ] **Step 4: Implement chat.py**

```python
# backend/app/api/chat.py
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.ai_engine import AIEngine
from app.config import config

logger = logging.getLogger(__name__)
router = APIRouter()

WALLPAPER_SYSTEM_PROMPT = """You are AIMWallpaper, an AI assistant that helps users create dynamic wallpapers for Wallpaper Engine.

You help users by:
1. Understanding their wallpaper requirements (effects, interactions, components)
2. Suggesting effects from the knowledge base
3. Building scene.json configurations
4. Generating SceneScript code for custom effects

Be conversational and ask clarifying questions when the user's intent is unclear.
Respond in the same language the user uses."""


def _get_ai_engine() -> AIEngine:
    return AIEngine.from_config(config)


# In-memory session storage (single-user app)
_sessions: dict[str, list[dict]] = {}


@router.websocket("/ws/chat/{project_id}")
async def chat_websocket(websocket: WebSocket, project_id: str):
    await websocket.accept()

    if project_id not in _sessions:
        _sessions[project_id] = []

    history = _sessions[project_id]

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

                # Send thinking indicator
                await websocket.send_json({"type": "ai_thinking", "content": "Processing your request..."})

                try:
                    engine = _get_ai_engine()
                    response = engine.chat(
                        system_prompt=WALLPAPER_SYSTEM_PROMPT,
                        messages=history,
                    )
                    history.append({"role": "assistant", "content": response})

                    await websocket.send_json({"type": "ai_message", "content": response})
                except Exception as e:
                    logger.error("Chat error: %s", e)
                    await websocket.send_json({"type": "error", "code": "LLM_ERROR", "message": str(e)})
            else:
                await websocket.send_json({"type": "error", "code": "UNKNOWN_TYPE", "message": f"Unknown message type: {msg_type}"})

    except WebSocketDisconnect:
        logger.info("Client disconnected from chat/%s", project_id)
```

- [ ] **Step 5: Register chat router in main.py**

Add to imports:
```python
from app.api.chat import router as chat_router
```

Add to router registrations:
```python
app.include_router(chat_router)
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd backend && pip install -e ".[dev]" && python -m pytest tests/test_api_chat.py -v
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/chat.py backend/app/models/chat.py backend/app/main.py backend/pyproject.toml backend/tests/test_api_chat.py
git commit -m "feat: add WebSocket chat API with multi-turn AI dialog"
```

---

## Task 7: Project Export & Preview API Endpoints

**Files:**
- Modify: `backend/app/api/project.py`
- Test: `backend/tests/test_api_projects.py` (add new tests)

Add `POST /api/projects/{id}/export` and `POST /api/projects/{id}/preview` endpoints.

- [ ] **Step 1: Write new tests**

Append to `backend/tests/test_api_projects.py`:

```python
from unittest.mock import patch, MagicMock


class TestProjectExportAndPreview:
    def test_export_project(self, client, app_db, tmp_data_dir):
        # Create a project first
        resp = client.post("/api/projects", json={"name": "Test Export"})
        project_id = resp.json()["project_id"]

        target = str(tmp_data_dir / "exported")
        resp = client.post(f"/api/projects/{project_id}/export", json={"target_dir": target})
        # Will fail if project has no generated files yet — expect 400
        assert resp.status_code in (200, 400)

    def test_preview_project_no_we(self, client, app_db, tmp_data_dir):
        resp = client.post("/api/projects", json={"name": "Test Preview"})
        project_id = resp.json()["project_id"]

        resp = client.post(f"/api/projects/{project_id}/preview")
        data = resp.json()
        # WE not installed in test env
        assert resp.status_code == 200
        assert data.get("preview_url") is None or data.get("available") is False
```

- [ ] **Step 2: Implement new endpoints in project.py**

Add to `backend/app/api/project.py`:

```python
from pydantic import BaseModel as PydanticBaseModel
from app.core.preview import PreviewService
from app.config import config as app_config


class ExportRequest(PydanticBaseModel):
    target_dir: str


@router.post("/{project_id}/export")
def export_project(project_id: str, body: ExportRequest):
    src = Path(app_config.storage.data_dir) / "projects" / project_id
    if not src.exists():
        raise HTTPException(status_code=400, detail="Project has no generated files")
    from app.core.project_generator import ProjectGenerator
    gen = ProjectGenerator(output_dir=str(Path(app_config.storage.data_dir) / "projects"))
    gen.export(project_id=project_id, target_dir=body.target_dir)
    return {"status": "exported", "target": body.target_dir}


@router.post("/{project_id}/preview")
def preview_project(project_id: str):
    project_path = Path(app_config.storage.data_dir) / "projects" / project_id / "project.json"
    svc = PreviewService.from_config(app_config)
    if not svc.is_available():
        return {"available": False, "preview_url": None, "message": "Wallpaper Engine not installed"}
    result = svc.preview(project_path=str(project_path), project_id=project_id)
    return {"available": True, "preview_url": result}
```

- [ ] **Step 3: Run tests**

```bash
cd backend && python -m pytest tests/test_api_projects.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/project.py backend/tests/test_api_projects.py
git commit -m "feat: add project export and preview API endpoints"
```

---

## Task 8: Phase 3 Integration Test

**Files:**
- Modify: `backend/tests/test_integration.py`

- [ ] **Step 1: Add Phase 3 integration tests**

Append to `backend/tests/test_integration.py`:

```python
from unittest.mock import patch, MagicMock


def test_scene_builder_to_project_pipeline(tmp_data_dir):
    """Build a scene, generate project, verify files."""
    from app.core.scene_builder import SceneBuilder
    from app.core.project_generator import ProjectGenerator

    builder = SceneBuilder()
    builder.set_camera(center=[0, 0, 0], eye=[0, 0, 1])
    builder.add_layer(name="background", image="bg.png")
    builder.add_effect("background", name="rain", passes=[{"combos": {"RAIN": 1}}])

    gen = ProjectGenerator(output_dir=str(tmp_data_dir / "projects"))
    result = gen.generate(project_id="integration_test", title="Integration Test Wallpaper",
                          scene_builder=builder, tags=["test"])

    import json
    scene = json.loads((result / "scene.json").read_text())
    assert len(scene["objects"]) == 1
    assert scene["objects"][0]["effects"][0]["name"] == "rain"

    project = json.loads((result / "project.json").read_text())
    assert project["title"] == "Integration Test Wallpaper"


@patch("app.core.ai_engine.litellm_completion")
def test_script_generator_pipeline(mock_completion):
    """Generate a SceneScript via mocked AI."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = 'export function update() { thisLayer.opacity = Math.sin(engine.runtime); }'
    mock_completion.return_value = mock_response

    from app.core.ai_engine import AIEngine
    from app.core.script_generator import ScriptGenerator

    engine = AIEngine(provider="openai", model="gpt-4o", api_key="test")
    gen = ScriptGenerator(ai_engine=engine)
    code = gen.generate("Pulse opacity")
    assert "thisLayer.opacity" in code


@patch("app.api.chat._get_ai_engine")
def test_chat_websocket_flow(mock_get_engine, client):
    """WebSocket chat sends thinking + ai_message."""
    mock_engine = MagicMock()
    mock_engine.chat.return_value = "Sure, I'll add rain!"
    mock_get_engine.return_value = mock_engine

    with client.websocket_connect("/ws/chat/integration_test") as ws:
        ws.send_json({"type": "user_message", "content": "Add rain effect"})
        messages = []
        for _ in range(5):
            msg = ws.receive_json()
            messages.append(msg)
            if msg["type"] == "ai_message":
                break
        assert any(m["type"] == "ai_message" and "rain" in m["content"].lower() for m in messages)
```

- [ ] **Step 2: Run ALL tests**

```bash
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_integration.py
git commit -m "feat: add Phase 3 integration tests for scene builder, script gen, and chat"
```

---

## Summary

After completing all 8 tasks, you will have:

- **SceneBuilder** — Fluent API for assembling WE scene.json from layers/effects
- **ProjectGenerator** — Full WE project file output with versioning and export
- **ScriptGenerator** — AI-powered SceneScript JS code generation with validation
- **PreviewService** — WE CLI preview with screenshot capture, graceful degradation
- **Chat WebSocket** — Multi-turn AI dialog at `/ws/chat/{project_id}`
- **Export/Preview APIs** — REST endpoints for project export and preview
- **Chat Message Models** — Pydantic types for WebSocket protocol

**Next phase:** Phase 4 — React Frontend
