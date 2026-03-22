from io import BytesIO


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
