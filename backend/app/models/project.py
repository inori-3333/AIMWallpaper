from pydantic import BaseModel


class WEProject(BaseModel):
    title: str
    type: str = "scene"
    file: str = "scene.json"
    description: str = ""
    tags: list[str] = []
    visibility: str = "private"
    model_config = {"extra": "allow"}
