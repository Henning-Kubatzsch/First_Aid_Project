# tests/unit/test_interfaces.py
from typing import Dict, List, Iterable, Optional, Any
from rag.interfaces import ChatModel, Chunker, Embedder, VectorIndex

# ---- Dummies ----

class DummyChat(ChatModel):
    def make_messages(
        self, user: str, system: Optional[str] = None, history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        if history:
            msgs.extend(history)
        msgs.append({"role": "user", "content": user})
        return msgs

    def chat(
        self, messages: List[Dict[str, str]], temperature: Optional[float] = None,
        top_p: Optional[float] = None, max_tokens: Optional[int] = None
    ) -> str:
        # echo last content
        return messages[-1]["content"]

    def chat_stream(
        self, messages: List[Dict[str, str]], temperature: Optional[float] = None,
        top_p: Optional[float] = None, max_tokens: Optional[int] = None
    ) -> Iterable[str]:
        out = self.chat(messages)
        for ch in out:
            yield ch


class DummyChunker(Chunker):
    def split(self, text: str, meta: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        meta = dict(meta or {})
        text = text.strip()
        if not text:
            return []
        # Minimal: ein Chunk, feste ID
        return [{"id": "deadbeefdeadbeef", "text": text, "meta": meta}]


class DummyEmbedder(Embedder):
    def embed(self, texts: List[str]) -> List[List[float]]:
        # Länge = 3, deterministisch aus len(text)
        return [[float(len(t)), 1.0, 0.0] for t in texts]

    def embed_one(self, text: str) -> List[float]:
        return self.embed([text])[0]


class DummyIndex(VectorIndex):
    def __init__(self):
        self._dim = None
        self._docs: List[Dict[str, Any]] = []

    def build(self, dim: int, space: str = "cosine") -> None:
        self._dim = dim

    def upsert(self, vectors: List[List[float]], metas: List[Dict[str, Any]]) -> None:
        assert self._dim is not None, "build() must be called before upsert()"
        assert len(vectors) == len(metas)
        for v, m in zip(vectors, metas):
            assert len(v) == self._dim
            self._docs.append({"text": m.get("text", ""), "meta": m, "vec": v})

    def query(self, vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        # Rückgabeform: [{'text': ..., 'meta': {...}, 'score': float}]
        res = []
        for d in self._docs[:k]:
            res.append({"text": d["text"], "meta": d["meta"], "score": 0.0})
        return res

    def save(self, path: str) -> None:
        # no-op
        pass

    def load(self, path: str) -> None:
        # no-op
        pass


# ---- Tests ----

def test_chatmodel_make_messages_and_chat_and_stream():
    cm = DummyChat()
    history = [{"role": "assistant", "content": "hi"}]
    msgs = cm.make_messages(user="hello", system="sys", history=history)
    assert msgs[0] == {"role": "system", "content": "sys"}
    assert msgs[-1] == {"role": "user", "content": "hello"}

    out = cm.chat(msgs)
    assert isinstance(out, str) and out == "hello"

    chunks = list(cm.chat_stream(msgs))
    assert "".join(chunks) == "hello"
    assert all(isinstance(s, str) for s in chunks)


def test_chunker_returns_required_shape_and_copies_meta():
    ch = DummyChunker()
    meta = {"a": 1}
    out = ch.split("  text  ", meta=meta)
    assert isinstance(out, list) and len(out) == 1
    item = out[0]
    assert set(item.keys()) == {"id", "text", "meta"}
    assert item["text"] == "text"
    # Meta kopiert, nicht referenziert
    meta["a"] = 2
    assert out[0]["meta"] == {"a": 1}


def test_embedder_shapes_and_embed_one_consistency():
    em = DummyEmbedder()
    vecs = em.embed(["a", "abcd"])
    assert len(vecs) == 2 and all(len(v) == 3 for v in vecs)
    assert em.embed_one("abcd") == vecs[1]


def test_vectorindex_minimal_lifecycle_and_query_shape():
    em = DummyEmbedder()
    idx = DummyIndex()
    idx.build(dim=3, space="cosine")
    texts = ["alpha", "beta"]
    vecs = em.embed(texts)
    metas = [{"text": t, "id": i} for i, t in enumerate(texts)]
    idx.upsert(vecs, metas)

    res = idx.query(vecs[0], k=2)
    assert len(res) == 2
    for r in res:
        assert set(r.keys()) == {"text", "meta", "score"}
        assert isinstance(r["score"], float)
