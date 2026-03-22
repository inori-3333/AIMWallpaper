import json
from app.models.scene import Scene, SceneObject, SceneEffect
from app.models.effect import EffectPass


class SceneBuilder:
    def __init__(self):
        self._camera: dict = {}
        self._general: dict = {}
        self._objects: list[SceneObject] = []

    @classmethod
    def from_scene(cls, scene: Scene) -> "SceneBuilder":
        builder = cls()
        builder._camera = scene.camera.copy() if scene.camera else {}
        builder._general = scene.general.copy() if scene.general else {}
        builder._objects = list(scene.objects)
        return builder

    def set_camera(self, center: list | None = None, eye: list | None = None):
        if center is not None:
            self._camera["center"] = center
        if eye is not None:
            self._camera["eye"] = eye

    def set_general(self, general: dict):
        self._general = general

    def add_layer(self, name: str, image: str = "", visible: bool = True,
                  origin: str = "0 0 0", scale: str = "1 1 1", **kwargs) -> SceneObject:
        obj = SceneObject(name=name, image=image, visible=visible,
                          origin=origin, scale=scale, **kwargs)
        self._objects.append(obj)
        return obj

    def remove_layer(self, name: str):
        self._objects = [o for o in self._objects if o.name != name]

    def _find_layer(self, name: str) -> SceneObject:
        for obj in self._objects:
            if obj.name == name:
                return obj
        raise ValueError(f"Layer '{name}' not found")

    def add_effect(self, layer_name: str, name: str = "", file: str = "",
                   passes: list[dict] | None = None) -> SceneEffect:
        layer = self._find_layer(layer_name)
        effect_passes = [EffectPass(**p) for p in (passes or [])]
        effect = SceneEffect(name=name, file=file, passes=effect_passes)
        layer.effects.append(effect)
        return effect

    def remove_effect(self, layer_name: str, effect_name: str):
        layer = self._find_layer(layer_name)
        layer.effects = [e for e in layer.effects if e.name != effect_name]

    def build(self) -> Scene:
        return Scene(camera=self._camera, general=self._general, objects=self._objects)

    def to_json(self, indent: int = 2) -> str:
        scene = self.build()
        return json.dumps(scene.model_dump(), indent=indent, ensure_ascii=False)
