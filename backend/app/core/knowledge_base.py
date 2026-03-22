import json
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.db.models import EffectPattern


class KnowledgeBaseService:
    def __init__(self, session: Session):
        self.session = session

    def create_pattern(
        self,
        name: str,
        description: str,
        category: str = "",
        tags: list[str] | None = None,
        confidence: float = 0.5,
        source: str = "",
        components: dict | None = None,
        params: dict | None = None,
    ) -> EffectPattern:
        pattern = EffectPattern(
            name=name,
            description=description,
            category=category,
            tags=",".join(tags) if tags else "",
            confidence=confidence,
            source=source,
            components=json.dumps(components or {}),
            params=json.dumps(params or {}),
        )
        self.session.add(pattern)
        self.session.commit()
        self.session.refresh(pattern)
        return pattern

    def get_pattern(self, pattern_id: int) -> EffectPattern | None:
        return self.session.get(EffectPattern, pattern_id)

    def list_patterns(self, category: str | None = None) -> list[EffectPattern]:
        stmt = select(EffectPattern)
        if category:
            stmt = stmt.where(EffectPattern.category == category)
        return list(self.session.execute(stmt).scalars().all())

    def verify_pattern(self, pattern_id: int) -> EffectPattern:
        pattern = self.session.get(EffectPattern, pattern_id)
        if pattern is None:
            raise ValueError(f"Pattern {pattern_id} not found")
        pattern.verified = True
        pattern.confidence = max(pattern.confidence, 0.9)
        self.session.commit()
        self.session.refresh(pattern)
        return pattern

    def delete_pattern(self, pattern_id: int) -> None:
        pattern = self.session.get(EffectPattern, pattern_id)
        if pattern:
            self.session.delete(pattern)
            self.session.commit()

    def update_confidence(self, pattern_id: int, delta: float) -> EffectPattern:
        pattern = self.session.get(EffectPattern, pattern_id)
        if pattern is None:
            raise ValueError(f"Pattern {pattern_id} not found")
        pattern.confidence = max(0.0, min(1.0, pattern.confidence + delta))
        self.session.commit()
        self.session.refresh(pattern)
        return pattern

    def search_patterns(self, query: str) -> list[EffectPattern]:
        """Simple text search across name, description, and tags."""
        like_query = f"%{query.lower()}%"
        stmt = select(EffectPattern).where(
            or_(
                EffectPattern.name.ilike(like_query),
                EffectPattern.description.ilike(like_query),
                EffectPattern.tags.ilike(like_query),
            )
        )
        return list(self.session.execute(stmt).scalars().all())
