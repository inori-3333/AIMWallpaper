from pydantic import BaseModel
from app.models.effect import EffectPass


class SceneEffect(BaseModel):
    name: str = ""
    file: str = ""
    passes: list[EffectPass] = []
    model_config = {"extra": "allow"}


class SceneObject(BaseModel):
    name: str = ""
    image: str = ""
    visible: bool = True
    origin: str = "0 0 0"
    scale: str = "1 1 1"
    angles: str = "0 0 0"
    effects: list[SceneEffect] = []
    model_config = {"extra": "allow"}


class Scene(BaseModel):
    camera: dict = {}
    general: dict = {}
    objects: list[SceneObject] = []
    model_config = {"extra": "allow"}
