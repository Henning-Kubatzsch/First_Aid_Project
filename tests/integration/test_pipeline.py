# tests/integration/test_pipeline.py
from fastapi.testclient import TestClient
import pytest

# ---- super-light stubs wired into rag.server during app lifespan ----

class _LLM:
    def __init__(self, cfg):  # cfg kommt aus load_llm_config
        self.cfg = cfg
    def make_messages(self, user: str, system: str | None = None, history=None):
        # minimal messages shape
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        if history:
            msgs.extend(history)
        msgs.append({"role": "user", "content": user})
        return msgs
    def chat(self, messages, **params) -> str:
        # Antworte kurz und deterministisch mit Schlüsselwörtern
        return "Apply a pressure bandage. Call 112."
    def chat_stream(self, messages, **params):
        # optional: nicht genutzt in diesem Minimaltest
        yield "Apply a pressure bandage. "
        yield "Call 112."

class _Embedder:
    def __init__(self, model_name: str, device: str = "cpu"): ...
    def embed_one(self, text: str):
        # deterministischer 3D-"Vektor"
        return [float(len(text)), 1.0, 0.0]

class _Index:
    def load(self, path: str): ...
    # nicht gebraucht für den Minimaltest

class _Retriever:
    def __init__(self, embedder, index, k: int = 5):
        self.k = k
    def search(self, q: str):
        # Fixe Mini-"Treffer", die in den Kontext wandern
        return [{"text": "Severe bleeding: apply a pressure bandage."},
                {"text": "Call 112."}]

@pytest.fixture()
def client(tmp_path, monkeypatch):
    import rag.server as server

    # temporäre YAML-Konfig, Pfad ins Servermodul setzen
    cfg_path = tmp_path / "rag.yaml"
    cfg_path.write_text(
        "llm:\n"
        f"  model_path: {tmp_path / 'dummy.gguf'}\n"
        "  family: qwen\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(server, "yaml_path", str(cfg_path), raising=False)

    # Schwere Komponenten durch Stubs ersetzen (direkt im server-Modul)
    monkeypatch.setattr(server, "LocalLLM", _LLM, raising=False)
    monkeypatch.setattr(server, "SBertEmbeddings", _Embedder, raising=False)
    monkeypatch.setattr(server, "HnswIndex", _Index, raising=False)
    monkeypatch.setattr(server, "Retriever", _Retriever, raising=False)

    # TestClient startet FastAPI inkl. lifespan()
    with TestClient(server.app) as c:
        yield c

@pytest.mark.integration
def test_pipeline_once_minimal(client):
    r = client.post("/rag_once", json={"q": "What to do for severe bleeding?"})
    assert r.status_code == 200
    ans = r.json()["answer"].lower()
    # minimaler, aber aussagekräftiger Check
    assert "bandage" in ans or "112" in ans

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}