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
        list_resp = client.get("/api/assets")
        ids = [a["asset_id"] for a in list_resp.json()]
        assert asset_id not in ids

    def test_delete_nonexistent(self, client, tmp_data_dir):
        resp = client.delete("/api/assets/nonexistent-id")
        assert resp.status_code == 404
