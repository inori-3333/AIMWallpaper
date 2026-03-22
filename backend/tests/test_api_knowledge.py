import pytest


class TestKnowledgeAPI:
    def _seed_pattern(self, client):
        resp = client.post("/api/knowledge/patterns", json={
            "name": "Rain",
            "description": "Rain effect",
            "category": "weather",
            "tags": ["rain", "weather"],
            "confidence": 0.7,
        })
        return resp.json()

    def test_list_patterns(self, client, knowledge_db):
        self._seed_pattern(client)
        resp = client.get("/api/knowledge/patterns")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_list_patterns_with_search(self, client, knowledge_db):
        self._seed_pattern(client)
        resp = client.get("/api/knowledge/patterns?q=rain")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_verify_pattern(self, client, knowledge_db):
        data = self._seed_pattern(client)
        pid = data["id"]
        resp = client.put(f"/api/knowledge/patterns/{pid}/verify")
        assert resp.status_code == 200
        assert resp.json()["verified"] is True
        assert resp.json()["confidence"] >= 0.9

    def test_delete_pattern(self, client, knowledge_db):
        data = self._seed_pattern(client)
        pid = data["id"]
        resp = client.delete(f"/api/knowledge/patterns/{pid}")
        assert resp.status_code == 200
        list_resp = client.get("/api/knowledge/patterns")
        ids = [p["id"] for p in list_resp.json()]
        assert pid not in ids

    def test_delete_nonexistent(self, client, knowledge_db):
        resp = client.delete("/api/knowledge/patterns/9999")
        assert resp.status_code == 404
