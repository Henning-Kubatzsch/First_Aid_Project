import hashlib
import math
import random
from pathlib import Path
import numpy as np
import pytest

# setting fixed random seed for reproducibility
@pytest.fixture(autouse=True)
def _fix_seed():
    random.seed(1337)
    np.random.seed(1337)

@pytest.fixture
def tiny_corpus():
    # Mini-Daten – bewusst kurz/variabel
    docs = [
        ("doc1", "Severe bleeding: apply a pressure bandage."),
        ("doc2", "Recovery position in case of unconsciousness."),
        ("doc3", "Call 112, describe the situation.")
    ]
    return docs

@pytest.fixture
def tmp_dir(tmp_path: Path):
    d = tmp_path / "work"
    d.mkdir()
    return d

@pytest.fixture
def fake_embed():
    # deterministic Pseudo-Embeddings from SHA256-Hash
    def _emb(texts, dim=16):
        vecs = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            # map bytes → floats
            arr = np.frombuffer(h, dtype=np.uint8)[:dim].astype(np.float32)
            # normalize
            norm = np.linalg.norm(arr) or 1.0
            vecs.append(arr / norm)
        return np.vstack(vecs)
    return _emb

_CREATED_LLAMAS = []

class DummyLlama:
    def __init__(self, **kwargs):
        self.init_kwargs = kwargs
        self.last_params = None
        self.last_messages = None
        _CREATED_LLAMAS.append(self)

    def create_chat_completion(self, *, messages, **params):
        self.last_messages = messages
        self.last_params = params
        if params.get("stream"):
            # stream: "hello"
            for piece in ["he", "llo"]:
                yield {"choices": [{"delta": {"content": piece}}]}
        else:
            # non-stream: Dict mit Content
            return {"choices": [{"message": {"content": "OK"}}]}

@pytest.fixture(autouse=True)
def patch_llama(monkeypatch):
    # wichtig: das im Modul gebundene Symbol patchen
    import rag.generator as g
    monkeypatch.setattr(g, "Llama", DummyLlama, raising=False)
    # optional den Dummy-Tracker exportieren für Tests
    g._CREATED_LLAMAS = _CREATED_LLAMAS
    yield
