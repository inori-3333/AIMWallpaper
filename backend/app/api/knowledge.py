from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_engine
from app.core.knowledge_base import KnowledgeBaseService

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class PatternCreate(BaseModel):
    name: str
    description: str = ""
    category: str = ""
    tags: list[str] = []
    confidence: float = 0.5
    source: str = ""


class PatternOut(BaseModel):
    id: int
    name: str
    description: str
    category: str
    tags: str
    confidence: float
    verified: bool


def _get_session() -> Session:
    return Session(get_engine())


@router.post("/patterns", response_model=PatternOut)
def create_pattern(body: PatternCreate):
    with _get_session() as session:
        kb = KnowledgeBaseService(session)
        p = kb.create_pattern(
            name=body.name,
            description=body.description,
            category=body.category,
            tags=body.tags,
            confidence=body.confidence,
            source=body.source,
        )
        return PatternOut(
            id=p.id, name=p.name, description=p.description,
            category=p.category, tags=p.tags, confidence=p.confidence, verified=p.verified,
        )


@router.get("/patterns", response_model=list[PatternOut])
def list_patterns(q: str | None = None, category: str | None = None):
    with _get_session() as session:
        kb = KnowledgeBaseService(session)
        if q:
            patterns = kb.search_patterns(q)
        else:
            patterns = kb.list_patterns(category=category)
        return [
            PatternOut(
                id=p.id, name=p.name, description=p.description,
                category=p.category, tags=p.tags, confidence=p.confidence, verified=p.verified,
            )
            for p in patterns
        ]


@router.put("/patterns/{pattern_id}/verify", response_model=PatternOut)
def verify_pattern(pattern_id: int):
    with _get_session() as session:
        kb = KnowledgeBaseService(session)
        try:
            p = kb.verify_pattern(pattern_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Pattern not found")
        return PatternOut(
            id=p.id, name=p.name, description=p.description,
            category=p.category, tags=p.tags, confidence=p.confidence, verified=p.verified,
        )


@router.delete("/patterns/{pattern_id}")
def delete_pattern(pattern_id: int):
    with _get_session() as session:
        kb = KnowledgeBaseService(session)
        if kb.get_pattern(pattern_id) is None:
            raise HTTPException(status_code=404, detail="Pattern not found")
        kb.delete_pattern(pattern_id)
        return {"status": "deleted"}
