from pydantic import BaseModel


class AssetResponse(BaseModel):
    asset_id: str
    filename: str
    content_type: str
    size: int


class ProjectCreate(BaseModel):
    name: str
    description: str = ""


class ProjectResponse(BaseModel):
    project_id: str
    name: str
    description: str = ""
    created_at: str
    version: int = 1


class ErrorResponse(BaseModel):
    detail: str
