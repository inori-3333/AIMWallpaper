import pytest
from sqlalchemy import select
from app.db.models import EffectPattern, FieldKnowledge, CompositionRule, ScriptSnippet, Project


class TestEffectPattern:
    def test_create_pattern(self, db_session):
        pattern = EffectPattern(
            name="Rain",
            description="Falling rain drops",
            category="weather",
            tags="rain,weather,particles",
            confidence=0.85,
            source="example_001",
            verified=False,
            components='{"type": "particle", "rate": 200}',
            params='{"rate": {"min": 50, "max": 500, "default": 200}}',
        )
        db_session.add(pattern)
        db_session.commit()

        result = db_session.execute(select(EffectPattern).where(EffectPattern.name == "Rain")).scalar_one()
        assert result.confidence == 0.85
        assert result.category == "weather"

    def test_pattern_defaults(self, db_session):
        pattern = EffectPattern(name="Test", description="test")
        db_session.add(pattern)
        db_session.commit()
        assert pattern.confidence == 0.5
        assert pattern.verified is False


class TestFieldKnowledge:
    def test_create_field(self, db_session):
        field = FieldKnowledge(
            path="objects[].effects[].passes[].combos",
            description="Shader combo flags",
            value_type="dict",
            examples='{"RAIN": 1}',
            confidence=0.9,
        )
        db_session.add(field)
        db_session.commit()
        assert field.id is not None


class TestCompositionRule:
    def test_create_rule(self, db_session):
        rule = CompositionRule(
            rule="Rain and snow effects should not be combined on the same layer",
            source="example_002",
            verified=True,
        )
        db_session.add(rule)
        db_session.commit()
        assert rule.verified is True


class TestScriptSnippet:
    def test_create_snippet(self, db_session):
        snippet = ScriptSnippet(
            name="clock_update",
            description="Updates a clock display every second",
            code='export function update(value) { /* ... */ }',
            api_used="thisLayer,engine.registerUpdate",
            tags="clock,time,component",
        )
        db_session.add(snippet)
        db_session.commit()
        assert snippet.name == "clock_update"


class TestProject:
    def test_create_project(self, db_session):
        proj = Project(name="Night City", description="Cyberpunk cityscape wallpaper")
        db_session.add(proj)
        db_session.commit()
        assert proj.id is not None
        assert proj.version == 1

    def test_project_timestamps(self, db_session):
        proj = Project(name="Test")
        db_session.add(proj)
        db_session.commit()
        assert proj.created_at is not None
        assert proj.updated_at is not None
