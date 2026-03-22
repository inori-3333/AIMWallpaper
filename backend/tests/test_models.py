import pytest
from app.models.scene import SceneObject, SceneEffect, Scene
from app.models.project import WEProject
from app.models.effect import EffectPass
from app.models.api import AssetResponse, ProjectResponse


class TestSceneModels:
    def test_scene_object_minimal(self):
        obj = SceneObject(name="bg", image="materials/bg.png")
        assert obj.name == "bg"
        assert obj.visible is True  # default
        assert obj.effects == []

    def test_scene_object_with_effects(self):
        effect = SceneEffect(
            name="rain",
            file="effects/rain.json",
            passes=[EffectPass(combos={"RAIN": 1}, textures=[])]
        )
        obj = SceneObject(name="bg", image="materials/bg.png", effects=[effect])
        assert len(obj.effects) == 1
        assert obj.effects[0].name == "rain"

    def test_scene_roundtrip(self):
        """Scene can be serialized to JSON and parsed back."""
        scene = Scene(
            camera={"center": [0, 0, 0], "eye": [0, 0, 1]},
            general={"properties": {"schemecolor": {"value": "0 0 0"}}},
            objects=[
                SceneObject(name="bg", image="materials/bg.png", origin="0 0 0", scale="1 1 1")
            ],
        )
        data = scene.model_dump()
        parsed = Scene.model_validate(data)
        assert parsed.objects[0].name == "bg"

    def test_scene_empty_objects_allowed(self):
        scene = Scene()
        assert scene.objects == []


class TestProjectModel:
    def test_project_minimal(self):
        proj = WEProject(
            title="My Wallpaper",
            type="web",
            file="scene.json",
        )
        assert proj.title == "My Wallpaper"

    def test_project_with_tags(self):
        proj = WEProject(
            title="Night City",
            type="scene",
            file="scene.json",
            tags=["cityscape", "night"],
        )
        assert "night" in proj.tags


class TestApiModels:
    def test_asset_response(self):
        resp = AssetResponse(
            asset_id="abc-123",
            filename="bg.png",
            content_type="image/png",
            size=1024,
        )
        assert resp.asset_id == "abc-123"

    def test_project_response(self):
        resp = ProjectResponse(
            project_id="p-1",
            name="Test",
            created_at="2026-01-01T00:00:00",
        )
        assert resp.project_id == "p-1"
