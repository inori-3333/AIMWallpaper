import pytest
from app.core.vector_store import VectorStore


@pytest.fixture
def vector_store(tmp_path):
    return VectorStore(persist_dir=str(tmp_path / "chroma"))


class TestVectorStore:
    def test_add_and_query(self, vector_store):
        vector_store.add(doc_id="pattern_1", text="rain drops falling from sky", embedding=[0.1, 0.2, 0.3, 0.4, 0.5], metadata={"category": "weather", "confidence": 0.85})
        results = vector_store.query(query_embedding=[0.1, 0.2, 0.3, 0.4, 0.5], n_results=5)
        assert len(results) >= 1
        assert results[0]["id"] == "pattern_1"

    def test_add_multiple_and_query(self, vector_store):
        vector_store.add("p1", "rain effect", [0.1, 0.2, 0.3, 0.0, 0.0], {"category": "weather"})
        vector_store.add("p2", "snow effect", [0.0, 0.2, 0.3, 0.1, 0.0], {"category": "weather"})
        vector_store.add("p3", "fire effect", [0.9, 0.0, 0.0, 0.1, 0.0], {"category": "particle"})
        results = vector_store.query([0.1, 0.2, 0.3, 0.0, 0.0], n_results=2)
        assert len(results) == 2
        assert results[0]["id"] == "p1"

    def test_delete(self, vector_store):
        vector_store.add("p1", "rain", [0.1, 0.2, 0.3, 0.0, 0.0], {})
        vector_store.delete("p1")
        results = vector_store.query([0.1, 0.2, 0.3, 0.0, 0.0], n_results=5)
        assert len(results) == 0

    def test_query_empty_store(self, vector_store):
        results = vector_store.query([0.1, 0.2, 0.3], n_results=5)
        assert results == []
