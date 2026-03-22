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
