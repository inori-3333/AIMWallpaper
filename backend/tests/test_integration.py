from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sample_project"


def test_full_workflow(client, tmp_data_dir, app_db):
    resp = client.get("/api/health")
    assert resp.status_code == 200

    resp = client.post("/api/projects", json={"name": "Integration Test"})
    assert resp.status_code == 200
    project_id = resp.json()["project_id"]

    resp = client.post(
        "/api/assets/upload",
        files={"file": ("bg.png", BytesIO(b"\x89PNG" + b"\x00" * 50), "image/png")},
    )
    assert resp.status_code == 200

    resp = client.get("/api/assets")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.get(f"/api/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Integration Test"

    resp = client.get("/api/config")
    assert resp.status_code == 200
    assert "wallpaper_engine" in resp.json()


def test_config_read(client):
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "storage" in data


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
