# tests/unit/test_retriever.py
import pytest
from rag.retriever import Retriever

# ---- Dummies ----

class DummyEmbedder:
    def __init__(self):
        self.calls = []

    def embed_one(self, text: str):
        self.calls.append(text)
        # deterministischer 2D-"Vektor": [len(text), 1.0]
        return [float(len(text)), 1.0]

    def embed(self, texts):
        return [[float(len(t)), 1.0] for t in texts]


class SpyIndex:
    def __init__(self):
        self.last_vector = None
        self.last_k = None
        self._result = [{"text": "docA", "meta": {"id": 1}, "score": 0.0}]

    def query(self, vector, k: int = 5):
        self.last_vector = vector
        self.last_k = k
        return list(self._result)  # kopie, um Seiteneffekte zu vermeiden

    # Unused by these tests but required by the VectorIndex protocol
    def build(self, dim: int, space: str = "cosine"): pass
    def upsert(self, vectors, metas): pass
    def save(self, path: str): pass
    def load(self, path: str): pass


# ---- Tests ----

def test_search_forwards_vector_and_k_and_returns_index_result():
    emb = DummyEmbedder()
    idx = SpyIndex()
    r = Retriever(embedder=emb, index=idx, k=2)

    out = r.search("hello")  # len("hello") = 5

    # embed_one genau einmal mit Original-Query
    assert emb.calls == ["hello"]

    # Vektor weitergereicht & k beachtet
    assert idx.last_vector == [5.0, 1.0]
    assert idx.last_k == 2

    # Passthrough der Index-Ergebnisse
    assert out == [{"text": "docA", "meta": {"id": 1}, "score": 0.0}]


def test_search_uses_default_k_5_when_not_overridden():
    emb = DummyEmbedder()
    idx = SpyIndex()
    r = Retriever(embedder=emb, index=idx)  # default k=5

    r.search("x")  # len = 1

    assert idx.last_vector == [1.0, 1.0]
    assert idx.last_k == 5


def test_search_handles_empty_query_string():
    emb = DummyEmbedder()
    idx = SpyIndex()
    r = Retriever(embedder=emb, index=idx, k=1)

    out = r.search("")  # len("") = 0

    assert emb.calls == [""]
    assert idx.last_vector == [0.0, 1.0]
    assert out == [{"text": "docA", "meta": {"id": 1}, "score": 0.0}]
