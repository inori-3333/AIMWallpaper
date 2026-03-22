import pytest
from pathlib import Path
from app.core.example_analyzer import ExampleAnalyzer

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sample_project"


class TestExampleAnalyzer:
    def test_parse_project_folder(self):
        analyzer = ExampleAnalyzer()
        result = analyzer.parse(FIXTURES_DIR)
        assert result["title"] == "Night City Rain"
        assert result["type"] == "scene"

    def test_extract_objects(self):
        analyzer = ExampleAnalyzer()
        result = analyzer.parse(FIXTURES_DIR)
        assert len(result["objects"]) == 2
        assert result["objects"][0]["name"] == "background"

    def test_extract_effects(self):
        analyzer = ExampleAnalyzer()
        result = analyzer.parse(FIXTURES_DIR)
        bg = result["objects"][0]
        assert len(bg["effects"]) == 1
        assert bg["effects"][0]["name"] == "rain"

    def test_extract_effect_details(self):
        analyzer = ExampleAnalyzer()
        result = analyzer.parse(FIXTURES_DIR)
        rain = result["objects"][0]["effects"][0]
        assert rain["passes"][0]["combos"] == {"RAIN": 1}
        assert "raindrop.png" in rain["passes"][0]["textures"][0]

    def test_summary(self):
        analyzer = ExampleAnalyzer()
        result = analyzer.parse(FIXTURES_DIR)
        summary = analyzer.summarize(result)
        assert "background" in summary
        assert "rain" in summary

    def test_parse_nonexistent_folder(self):
        analyzer = ExampleAnalyzer()
        with pytest.raises(FileNotFoundError):
            analyzer.parse(Path("/nonexistent/path"))

    def test_parse_missing_scene_json(self, tmp_path):
        (tmp_path / "project.json").write_text('{"title": "test", "type": "scene", "file": "scene.json"}')
        analyzer = ExampleAnalyzer()
        with pytest.raises(FileNotFoundError, match="scene.json"):
            analyzer.parse(tmp_path)
