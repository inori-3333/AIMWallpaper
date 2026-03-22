import json
import pytest
from app.core.scene_builder import SceneBuilder
from app.models.scene import Scene, SceneObject, SceneEffect


class TestSceneBuilder:
    def test_create_empty_scene(self):
        builder = SceneBuilder()
        scene = builder.build()
        assert isinstance(scene, Scene)
        assert scene.objects == []

    def test_add_image_layer(self):
        builder = SceneBuilder()
        builder.add_layer(name="background", image="materials/bg.png")
        scene = builder.build()
        assert len(scene.objects) == 1
        assert scene.objects[0].name == "background"
        assert scene.objects[0].image == "materials/bg.png"

    def test_add_effect_to_layer(self):
        builder = SceneBuilder()
        builder.add_layer(name="bg", image="materials/bg.png")
        builder.add_effect("bg", name="rain", file="effects/rain.json",
                           passes=[{"combos": {"RAIN": 1}, "textures": ["materials/raindrop.png"]}])
        scene = builder.build()
        assert len(scene.objects[0].effects) == 1
        assert scene.objects[0].effects[0].name == "rain"

    def test_add_effect_to_nonexistent_layer_raises(self):
        builder = SceneBuilder()
        with pytest.raises(ValueError, match="not found"):
            builder.add_effect("missing", name="rain")

    def test_set_camera(self):
        builder = SceneBuilder()
        builder.set_camera(center=[0, 0, 0], eye=[0, 0, 1])
        scene = builder.build()
        assert scene.camera["center"] == [0, 0, 0]

    def test_set_general_properties(self):
        builder = SceneBuilder()
        builder.set_general({"properties": {"schemecolor": {"value": "0.2 0.1 0.3"}}})
        scene = builder.build()
        assert "schemecolor" in scene.general["properties"]

    def test_to_json(self):
        builder = SceneBuilder()
        builder.add_layer(name="bg", image="bg.png")
        result = builder.to_json()
        parsed = json.loads(result)
        assert "objects" in parsed
        assert parsed["objects"][0]["name"] == "bg"

    def test_from_scene(self):
        original = Scene(
            camera={"center": [0, 0, 0]},
            objects=[SceneObject(name="bg", image="bg.png")]
        )
        builder = SceneBuilder.from_scene(original)
        builder.add_layer(name="overlay", image="overlay.png")
        scene = builder.build()
        assert len(scene.objects) == 2

    def test_remove_layer(self):
        builder = SceneBuilder()
        builder.add_layer(name="bg", image="bg.png")
        builder.add_layer(name="overlay", image="overlay.png")
        builder.remove_layer("bg")
        scene = builder.build()
        assert len(scene.objects) == 1
        assert scene.objects[0].name == "overlay"

    def test_remove_effect(self):
        builder = SceneBuilder()
        builder.add_layer(name="bg", image="bg.png")
        builder.add_effect("bg", name="rain")
        builder.add_effect("bg", name="blur")
        builder.remove_effect("bg", "rain")
        scene = builder.build()
        assert len(scene.objects[0].effects) == 1
        assert scene.objects[0].effects[0].name == "blur"
