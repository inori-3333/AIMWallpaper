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
