from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.orm import Session
from app.db.database import get_engine
from app.db.models import Project
from app.models.api import ProjectCreate, ProjectResponse
from app.config import config as app_config

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _get_session() -> Session:
    return Session(get_engine())


@router.post("", response_model=ProjectResponse)
def create_project(body: ProjectCreate):
    with _get_session() as session:
        proj = Project(name=body.name, description=body.description)
        session.add(proj)
        session.commit()
        session.refresh(proj)
        return ProjectResponse(
            project_id=str(proj.id),
            name=proj.name,
            description=proj.description,
            created_at=proj.created_at.isoformat(),
            version=proj.version,
        )


@router.get("", response_model=list[ProjectResponse])
def list_projects():
    with _get_session() as session:
        projects = session.query(Project).all()
        return [
            ProjectResponse(
                project_id=str(p.id),
                name=p.name,
                description=p.description,
                created_at=p.created_at.isoformat(),
                version=p.version,
            )
            for p in projects
        ]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str):
    with _get_session() as session:
        proj = session.get(Project, int(project_id))
        if proj is None:
            raise HTTPException(status_code=404, detail="Project not found")
        return ProjectResponse(
            project_id=str(proj.id),
            name=proj.name,
            description=proj.description,
            created_at=proj.created_at.isoformat(),
            version=proj.version,
        )


@router.post("/{project_id}/undo")
def undo_project(project_id: str):
    with _get_session() as session:
        proj = session.get(Project, int(project_id))
        if proj is None:
            raise HTTPException(status_code=404, detail="Project not found")
        if proj.version <= 1:
            raise HTTPException(status_code=400, detail="Nothing to undo")
        proj.version -= 1
        session.commit()
        return {"status": "ok", "version": proj.version}


class ExportRequest(PydanticBaseModel):
    target_dir: str


@router.post("/{project_id}/export")
def export_project(project_id: str, body: ExportRequest):
    src = Path(app_config.storage.data_dir) / "projects" / project_id
    if not src.exists():
        raise HTTPException(status_code=400, detail="Project has no generated files")
    from app.core.project_generator import ProjectGenerator
    gen = ProjectGenerator(output_dir=str(Path(app_config.storage.data_dir) / "projects"))
    gen.export(project_id=project_id, target_dir=body.target_dir)
    return {"status": "exported", "target": body.target_dir}


@router.post("/{project_id}/preview")
def preview_project(project_id: str):
    from app.core.preview import PreviewService
    project_path = Path(app_config.storage.data_dir) / "projects" / project_id / "project.json"
    svc = PreviewService.from_config(app_config)
    if not svc.is_available():
        return {"available": False, "preview_url": None, "message": "Wallpaper Engine not installed"}
    result = svc.preview(project_path=str(project_path), project_id=project_id)
    return {"available": True, "preview_url": result}
