import pytest
from app.core.knowledge_base import KnowledgeBaseService
from app.db.models import EffectPattern


class TestPatternCRUD:
    def test_create_pattern(self, db_session):
        kb = KnowledgeBaseService(db_session)
        pattern = kb.create_pattern(
            name="Rain",
            description="Rain drops falling",
            category="weather",
            tags=["rain", "weather"],
            confidence=0.85,
            components={"type": "particle"},
            params={"rate": {"min": 50, "max": 500}},
        )
        assert pattern.id is not None
        assert pattern.name == "Rain"

    def test_get_pattern(self, db_session):
        kb = KnowledgeBaseService(db_session)
        created = kb.create_pattern(name="Snow", description="Snowfall", category="weather")
        fetched = kb.get_pattern(created.id)
        assert fetched is not None
        assert fetched.name == "Snow"

    def test_get_pattern_not_found(self, db_session):
        kb = KnowledgeBaseService(db_session)
        assert kb.get_pattern(999) is None

    def test_list_patterns(self, db_session):
        kb = KnowledgeBaseService(db_session)
        kb.create_pattern(name="Rain", description="Rain", category="weather")
        kb.create_pattern(name="Fire", description="Fire", category="particle")
        patterns = kb.list_patterns()
        assert len(patterns) == 2

    def test_list_patterns_by_category(self, db_session):
        kb = KnowledgeBaseService(db_session)
        kb.create_pattern(name="Rain", description="Rain", category="weather")
        kb.create_pattern(name="Fire", description="Fire", category="particle")
        patterns = kb.list_patterns(category="weather")
        assert len(patterns) == 1
        assert patterns[0].name == "Rain"

    def test_verify_pattern(self, db_session):
        kb = KnowledgeBaseService(db_session)
        p = kb.create_pattern(name="Rain", description="Rain", confidence=0.6)
        updated = kb.verify_pattern(p.id)
        assert updated.verified is True
        assert updated.confidence >= 0.9

    def test_delete_pattern(self, db_session):
        kb = KnowledgeBaseService(db_session)
        p = kb.create_pattern(name="Rain", description="Rain")
        kb.delete_pattern(p.id)
        assert kb.get_pattern(p.id) is None

    def test_update_confidence(self, db_session):
        kb = KnowledgeBaseService(db_session)
        p = kb.create_pattern(name="Rain", description="Rain", confidence=0.5)
        updated = kb.update_confidence(p.id, delta=0.1)
        assert updated.confidence == pytest.approx(0.6)

    def test_confidence_clamped(self, db_session):
        kb = KnowledgeBaseService(db_session)
        p = kb.create_pattern(name="Rain", description="Rain", confidence=0.95)
        updated = kb.update_confidence(p.id, delta=0.2)
        assert updated.confidence == 1.0

        updated2 = kb.update_confidence(p.id, delta=-2.0)
        assert updated2.confidence == 0.0


class TestSearchPatterns:
    def test_search_by_name(self, db_session):
        kb = KnowledgeBaseService(db_session)
        kb.create_pattern(name="Rain Effect", description="Falling rain")
        kb.create_pattern(name="Snow Effect", description="Falling snow")
        results = kb.search_patterns("rain")
        assert len(results) == 1
        assert results[0].name == "Rain Effect"

    def test_search_by_tags(self, db_session):
        kb = KnowledgeBaseService(db_session)
        kb.create_pattern(name="Glow", description="Light glow", tags=["light", "glow"])
        kb.create_pattern(name="Rain", description="Rain", tags=["weather"])
        results = kb.search_patterns("glow")
        assert len(results) == 1
