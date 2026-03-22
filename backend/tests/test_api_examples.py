import pytest
import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sample_project"


class TestExamplesAPI:
    def test_import_example_from_path(self, client, tmp_data_dir):
        resp = client.post("/api/examples/import", json={"path": str(FIXTURES_DIR)})
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Night City Rain"
        assert data["object_count"] == 2

    def test_import_nonexistent_path(self, client, tmp_data_dir):
        resp = client.post("/api/examples/import", json={"path": "/nonexistent/path"})
        assert resp.status_code == 400

    def test_list_examples(self, client, tmp_data_dir):
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
