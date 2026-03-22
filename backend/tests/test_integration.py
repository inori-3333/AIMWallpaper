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
