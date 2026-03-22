from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class EffectPattern(Base):
    __tablename__ = "effect_patterns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(100), default="")
    tags: Mapped[str] = mapped_column(Text, default="")  # comma-separated
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    source: Mapped[str] = mapped_column(String(200), default="")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    components: Mapped[str] = mapped_column(Text, default="{}")  # JSON string
    params: Mapped[str] = mapped_column(Text, default="{}")  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class FieldKnowledge(Base):
    __tablename__ = "field_knowledge"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    value_type: Mapped[str] = mapped_column(String(50), default="")
    examples: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    user_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class CompositionRule(Base):
    __tablename__ = "composition_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(200), default="")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    user_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ScriptSnippet(Base):
    __tablename__ = "script_snippets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    code: Mapped[str] = mapped_column(Text, default="")
    api_used: Mapped[str] = mapped_column(Text, default="")  # comma-separated
    tags: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    scene_json: Mapped[str] = mapped_column(Text, default="{}")
    project_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
