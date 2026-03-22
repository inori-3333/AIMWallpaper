import chromadb
from pathlib import Path


class VectorStore:
    def __init__(self, persist_dir: str = "./data/chroma", collection_name: str = "effect_patterns"):
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, doc_id: str, text: str, embedding: list[float], metadata: dict | None = None):
        meta = metadata if metadata else None
        self._collection.upsert(ids=[doc_id], documents=[text], embeddings=[embedding], metadatas=[meta])

    def query(self, query_embedding: list[float], n_results: int = 5, where: dict | None = None) -> list[dict]:
        kwargs = {"query_embeddings": [query_embedding], "n_results": n_results}
        if where:
            kwargs["where"] = where
        try:
            results = self._collection.query(**kwargs)
        except Exception:
            return []
        if not results["ids"] or not results["ids"][0]:
            return []
        output = []
        for i, doc_id in enumerate(results["ids"][0]):
            output.append({
                "id": doc_id,
                "document": results["documents"][0][i] if results["documents"] else "",
                "distance": results["distances"][0][i] if results["distances"] else 0,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            })
        return output

    def delete(self, doc_id: str):
        try:
            self._collection.delete(ids=[doc_id])
        except Exception:
            pass

    def count(self) -> int:
        return self._collection.count()
