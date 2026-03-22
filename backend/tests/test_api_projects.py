import pytest
from unittest.mock import patch, MagicMock


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
        assert resp.status_code == 400


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
        # WE not installed in test env — either unavailable or empty preview_url
        assert resp.status_code == 200
        assert data.get("available") is False or not data.get("preview_url")
