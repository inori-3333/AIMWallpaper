import json
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


@pytest.fixture
def uploads_dir(tmp_path):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    return uploads


@pytest.fixture
def asset_with_image(uploads_dir):
    """Create a fake asset entry and image file, return asset_id."""
    asset_id = str(uuid.uuid4())
    stored_name = f"{asset_id}.png"
    (uploads_dir / stored_name).write_bytes(FAKE_PNG)
    index = [
        {
            "asset_id": asset_id,
            "filename": "photo.png",
            "stored_name": stored_name,
            "content_type": "image/png",
            "size": len(FAKE_PNG),
        }
    ]
    (uploads_dir / "assets.json").write_text(json.dumps(index), encoding="utf-8")
    return asset_id


class TestSeparateForeground:
    def test_success(self, uploads_dir, asset_with_image):
        from app.core.image_separator import separate_foreground

        fg_png = b"\x89PNG\r\n\x1a\nFOREGROUND"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = fg_png

        with patch("app.core.image_separator.httpx.post", return_value=mock_response):
            result = separate_foreground(
                asset_id=asset_with_image,
                api_key="test-key",
                uploads_dir=uploads_dir,
            )

        assert result["background_asset_id"] == asset_with_image
        assert result["foreground_asset_id"] != asset_with_image
        assert result["fg_layer_name"] == "foreground"
        assert result["bg_layer_name"] == "background"

        # Verify foreground file was saved
        fg_id = result["foreground_asset_id"]
        fg_file = uploads_dir / f"{fg_id}.png"
        assert fg_file.exists()
        assert fg_file.read_bytes() == fg_png

        # Verify asset index was updated
        index = json.loads((uploads_dir / "assets.json").read_text(encoding="utf-8"))
        fg_entries = [a for a in index if a["asset_id"] == fg_id]
        assert len(fg_entries) == 1
        assert "foreground" in fg_entries[0]["filename"]

    def test_asset_not_found(self, uploads_dir):
        from app.core.image_separator import separate_foreground

        (uploads_dir / "assets.json").write_text("[]", encoding="utf-8")

        with pytest.raises(FileNotFoundError, match="not found"):
            separate_foreground(
                asset_id="nonexistent",
                api_key="test-key",
                uploads_dir=uploads_dir,
            )

    def test_api_failure(self, uploads_dir, asset_with_image):
        from app.core.image_separator import separate_foreground

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Invalid API key"
        mock_response.raise_for_status = MagicMock(
            side_effect=Exception("403 Forbidden")
        )

        with patch("app.core.image_separator.httpx.post", return_value=mock_response):
            with pytest.raises(Exception, match="403"):
                separate_foreground(
                    asset_id=asset_with_image,
                    api_key="bad-key",
                    uploads_dir=uploads_dir,
                )

    def test_unsupported_format(self, uploads_dir):
        """Non-image files should be rejected before calling remove.bg."""
        from app.core.image_separator import separate_foreground

        asset_id = str(uuid.uuid4())
        stored_name = f"{asset_id}.txt"
        (uploads_dir / stored_name).write_bytes(b"not an image")
        index = [{
            "asset_id": asset_id,
            "filename": "notes.txt",
            "stored_name": stored_name,
            "content_type": "text/plain",
            "size": 12,
        }]
        (uploads_dir / "assets.json").write_text(json.dumps(index), encoding="utf-8")

        with pytest.raises(ValueError, match="Unsupported image format"):
            separate_foreground(
                asset_id=asset_id,
                api_key="test-key",
                uploads_dir=uploads_dir,
            )
