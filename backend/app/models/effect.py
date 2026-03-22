from pydantic import BaseModel


class EffectPass(BaseModel):
    combos: dict = {}
    textures: list[str] = []
    constantshadervalues: dict = {}
    model_config = {"extra": "allow"}
