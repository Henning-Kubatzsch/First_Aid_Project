# tests/unit/test_server.py
from fastapi.testclient import TestClient
import pytest

# ---- lightweight stubs used during app lifespan ----

class _DummyLocalLLM:
    def __init__(self, cfg):
        self.cfg = cfg
        self._msgs = None

    def make_messages(self, user: str, system: str | None = None, history=None):
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        if history:
            msgs.extend(history)
        msgs.append({"role": "user", "content": user})
        self._msgs = msgs
        return msgs

    def chat(self, messages, **params) -> str:
        return "OK"

    def chat_stream(self, messages, **params):
        # MUST yield strings because server encodes them with .encode("utf-8")
        yield "he"
        yield "llo"


class _DummySBertEmbeddings:
    def __init__(self, model_name: str, device: str = "cpu"):
        self.model_name = model_name
        self.device = device

    def embed_one(self, text: str):
        return [1.0, 0.0, 0.0]


class _DummyIndex:
    def load(self, path: str):
        return None


class _DummyRetriever:
    def __init__(self, embedder, index, k: int = 5):
        self.k = k

    def search(self, q: str):
        return [{"text": "Doc A"}, {"text": "Doc B"}]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    import rag.server as server

    # temp config file
    cfg_path = tmp_path / "rag.yaml"
    cfg_path.write_text(
        "llm:\n"
        f"  model_path: {tmp_path / 'dummy.gguf'}\n"
        "  family: qwen\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(server, "yaml_path", str(cfg_path), raising=False)

    # patch heavy deps with stubs
    monkeypatch.setattr(server, "LocalLLM", _DummyLocalLLM, raising=False)
    monkeypatch.setattr(server, "SBertEmbeddings", _DummySBertEmbeddings, raising=False)
    monkeypatch.setattr(server, "HnswIndex", _DummyIndex, raising=False)
    monkeypatch.setattr(server, "Retriever", _DummyRetriever, raising=False)

    with TestClient(server.app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_rag_streaming_ok(client):
    r = client.post("/rag", json={"q": "What is this?"})
    assert r.status_code == 200
    assert r.text == "hello"


def test_rag_once_ok(client):
    r = client.post("/rag_once", json={"q": "What is this?"})
    assert r.status_code == 200
    assert r.json() == {"answer": "OK"}


def test_rag_streaming_handles_errors(client, monkeypatch):
    import rag.server as server

    def _boom(messages, **params):
        raise ValueError("kaboom")

    monkeypatch.setattr(server.S.llm, "chat_stream", _boom, raising=False)

    r = client.post("/rag", json={"q": "cause error"})
    assert r.status_code == 200
    assert "[stream-error] ValueError: kaboom" in r.text
