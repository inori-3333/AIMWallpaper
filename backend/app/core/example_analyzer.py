import json
from pathlib import Path


class ExampleAnalyzer:
    def parse(self, project_path: Path) -> dict:
        project_path = Path(project_path)
        if not project_path.exists():
            raise FileNotFoundError(f"Project path not found: {project_path}")
        project_file = project_path / "project.json"
        if project_file.exists():
            project_data = json.loads(project_file.read_text(encoding="utf-8"))
        else:
            project_data = {}
        scene_file_name = project_data.get("file", "scene.json")
        scene_file = project_path / scene_file_name
        if not scene_file.exists():
            raise FileNotFoundError(f"scene.json not found at: {scene_file}")
        scene_data = json.loads(scene_file.read_text(encoding="utf-8"))
        return {
            "title": project_data.get("title", ""),
            "type": project_data.get("type", "scene"),
            "tags": project_data.get("tags", []),
            "path": str(project_path),
            "camera": scene_data.get("camera", {}),
            "general": scene_data.get("general", {}),
            "objects": scene_data.get("objects", []),
        }

    def summarize(self, parsed: dict) -> str:
        parts = [f"Title: {parsed.get('title', 'Untitled')}"]
        tags = parsed.get("tags", [])
        if tags:
            parts.append(f"Tags: {', '.join(tags)}")
        for obj in parsed.get("objects", []):
            obj_desc = f"Layer '{obj.get('name', 'unnamed')}'"
            effects = obj.get("effects", [])
            if effects:
                effect_names = [e.get("name", "unnamed") for e in effects]
                obj_desc += f" with effects: {', '.join(effect_names)}"
            parts.append(obj_desc)
        return ". ".join(parts)
