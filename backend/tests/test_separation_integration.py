"""Integration test: full flow from asset creation through separation and layer assembly."""

import json
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
FAKE_FG_PNG = b"\x89PNG\r\n\x1a\nFOREGROUND_RESULT"


@pytest.fixture
def populated_uploads(tmp_data_dir):
    """Create uploads dir with one image asset, return (asset_id, uploads_dir)."""
    uploads = tmp_data_dir / "uploads"
    asset_id = str(uuid.uuid4())
    stored = f"{asset_id}.png"
    (uploads / stored).write_bytes(FAKE_PNG)
    index = [{
        "asset_id": asset_id,
        "filename": "test_photo.jpg",
        "stored_name": stored,
        "content_type": "image/jpeg",
        "size": len(FAKE_PNG),
    }]
    (uploads / "assets.json").write_text(json.dumps(index), encoding="utf-8")
    return asset_id, uploads


class TestSeparationIntegration:
    def test_full_separation_flow(self, populated_uploads):
        """Test: separate_foreground creates fg asset and updates index."""
        asset_id, uploads = populated_uploads

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = FAKE_FG_PNG
        mock_response.raise_for_status = MagicMock()

        with patch("app.core.image_separator.httpx.post", return_value=mock_response):
            from app.core.image_separator import separate_foreground
            result = separate_foreground(
                asset_id=asset_id,
                api_key="test-key",
                uploads_dir=uploads,
            )

        # Both assets exist in index
        index = json.loads((uploads / "assets.json").read_text(encoding="utf-8"))
        assert len(index) == 2

        bg_entry = next(a for a in index if a["asset_id"] == result["background_asset_id"])
        fg_entry = next(a for a in index if a["asset_id"] == result["foreground_asset_id"])

        assert bg_entry["filename"] == "test_photo.jpg"
        assert "foreground" in fg_entry["filename"]

        # Foreground file exists on disk
        fg_path = uploads / fg_entry["stored_name"]
        assert fg_path.exists()
        assert fg_path.read_bytes() == FAKE_FG_PNG

        # Result includes stored_name fields for layer assembly
        assert result["fg_stored_name"] == fg_entry["stored_name"]
        assert result["bg_stored_name"] == bg_entry["stored_name"]

    def test_layer_assembly(self, populated_uploads, tmp_data_dir):
        """Test: _assemble_layers creates scene.pkg with both layers."""
        asset_id, uploads = populated_uploads

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = FAKE_FG_PNG
        mock_response.raise_for_status = MagicMock()

        with patch("app.core.image_separator.httpx.post", return_value=mock_response):
            from app.core.image_separator import separate_foreground
            result = separate_foreground(
                asset_id=asset_id,
                api_key="test-key",
                uploads_dir=uploads,
            )

        # Create projects dir
        projects_dir = tmp_data_dir / "projects"
        projects_dir.mkdir(exist_ok=True)

        from app.core.scene_builder import SceneBuilder
        from app.core.project_generator import ProjectGenerator

        builder = SceneBuilder()
        builder.add_layer(name=result["bg_layer_name"], image=result["bg_stored_name"])
        builder.add_layer(name=result["fg_layer_name"], image=result["fg_stored_name"])

        generator = ProjectGenerator(
            output_dir=str(projects_dir),
            assets_dir=str(uploads),
        )
        project_dir = generator.generate(
            project_id="test-project",
            title="test-project",
            scene_builder=builder,
        )

        # Verify scene.pkg and project.json were created
        assert (project_dir / "scene.pkg").exists()
        assert (project_dir / "project.json").exists()

        # Verify scene.pkg contains scene.json with both layers
        from app.core.scene_packager import unpack
        pkg_files = unpack((project_dir / "scene.pkg").read_bytes())
        assert "scene.json" in pkg_files
        scene = json.loads(pkg_files["scene.json"])
        layer_names = [obj["name"] for obj in scene["objects"]]
        assert "background" in layer_names
        assert "foreground" in layer_names
        assert layer_names.index("background") < layer_names.index("foreground")
