# tests/test_cli.py
import types
import pytest
from typer.testing import CliRunner

# Import der CLI-App
import rag.cli as cli

runner = CliRunner()

# -----------------------------
# Fixtures: LLM-Mocks
# -----------------------------

@pytest.fixture
def llm_mocks(monkeypatch):
    """Mockt load_llm_config + LocalLLM, damit keine echten GGUF/llama.cpp genutzt werden."""
    # load_llm_config -> simple Namespace
    monkeypatch.setattr(
        cli, "load_llm_config", lambda path: types.SimpleNamespace(max_tokens=123), raising=True
    )

    class DummyLLM:
        def __init__(self, cfg):
            self.cfg = cfg
        def make_messages(self, *, user, system):
            # wir geben einfach eine Liste zurück, die chat/chat_stream akzeptieren
            return [("system", system), ("user", user)]
        def chat(self, msgs, max_tokens=None, **_):
            # deterministische Antwort (prüfbar im Test)
            return f"ANSWER(max_tokens={max_tokens})"
        def chat_stream(self, msgs, **_):
            for t in ["A", "B", "C"]:
                yield t

    monkeypatch.setattr(cli, "LocalLLM", DummyLLM, raising=True)
    return DummyLLM


# -----------------------------
# Fixtures: Retriever-Stack (Embedder, Index, Retriever)
# -----------------------------
@pytest.fixture
def retriever_stack_mocks(monkeypatch):
    """
    Patcht SBertEmbeddings, HnswIndex, Retriever an Verbrauchsort UND an den Ursprungsmodulen,
    damit sicher NUR die Dummies verwendet werden.
    """
    # Ursprungs-Module nachladen zum Doppelt-Patchen
    import rag.embed as embed_mod
    import rag.indexer as indexer_mod
    import rag.retriever as retriever_mod

    seen = {"embed_model": None, "k": None, "question": None, "queried_k": None}

    class DummyEmbed:
        def __init__(self, model_name):
            seen["embed_model"] = model_name
        def embed(self, texts):
            return [[0.0, 1.0, 2.0] for _ in texts]
        def embed_one(self, text):
            return [0.0, 1.0, 2.0]

    class DummyIndex:
        def __init__(self):
            self.loaded_dir = None
        def load(self, index_dir):
            self.loaded_dir = index_dir
        def query(self, vector, k=5):
            seen["queried_k"] = k
            return [
                {"text": "Doc One", "meta": {"id": 1}, "score": 0.1},
                {"text": "Doc Two", "meta": {"id": 2}, "score": 0.2},
            ]

    class DummyRetriever:
        def __init__(self, embedder, index, k):
            self.embedder = embedder
            self.index = index
            self.k = k
            seen["k"] = k
        def search(self, question):
            seen["question"] = question
            vec = self.embedder.embed_one(question)
            return self.index.query(vec, k=self.k)

    # Verbrauchsort patchen
    monkeypatch.setattr(cli, "SBertEmbeddings", DummyEmbed, raising=True)
    monkeypatch.setattr(cli, "HnswIndex", DummyIndex, raising=True)
    monkeypatch.setattr(cli, "Retriever", DummyRetriever, raising=True)
    # Ursprungsmodul patchen (falls intern referenziert)
    monkeypatch.setattr(embed_mod, "SBertEmbeddings", DummyEmbed, raising=True)
    monkeypatch.setattr(indexer_mod, "HnswIndex", DummyIndex, raising=True)
    monkeypatch.setattr(retriever_mod, "Retriever", DummyRetriever, raising=True)

    return seen


# -----------------------------
# ingest
# -----------------------------

def test_ingest_calls_builder_and_echo(monkeypatch, tmp_path):
    called = {"args": None}

    def fake_builder(*, docs_dir, out_dir, model_name):
        called["args"] = (docs_dir, out_dir, model_name)

    # CLI importiert build_erc_index aus scripts.build_index
    monkeypatch.setattr(cli, "build_erc_index", fake_builder, raising=True)

    docs = tmp_path / "docs"
    out = tmp_path / "index"
    res = runner.invoke(
        cli.app,
        ["ingest", "--docs", str(docs), "--out", str(out), "--embed-model", "my-embedder"],
    )
    assert res.exit_code == 0, res.output
    assert f"Index written to {out}" in res.output
    assert called["args"] == (str(docs), str(out), "my-embedder")


# -----------------------------
# ask (Retrieval + LLM Chat)
# -----------------------------
def test_ask_builds_context_uses_retriever_and_llm(llm_mocks, retriever_stack_mocks):
    res = runner.invoke(
        cli.app,
        ["ask", "How to stop bleeding?", "--k", "3", "--embed-model", "sbert-x"],
    )
    assert res.exit_code == 0, res.output
    # Antwort des Dummy-LLM
    assert "ANSWER(max_tokens=123)" in res.output
    # Parameter durch den gesamten Stack gereicht
    assert retriever_stack_mocks["embed_model"] == "sbert-x"
    assert retriever_stack_mocks["k"] == 3
    assert retriever_stack_mocks["queried_k"] == 3
    assert retriever_stack_mocks["question"] == "How to stop bleeding?"


@pytest.mark.parametrize(
    "extra_args, expected_model",
    [
        ([], "sentence-transformers/all-MiniLM-L6-v2"),   # Default
        (["--embed-model", "sbert-x"], "sbert-x"),        # Override
    ],
)
def test_ask_embedding_model_propagation(llm_mocks, retriever_stack_mocks, extra_args, expected_model):
    args = ["ask", "How to stop bleeding?", "--k", "2"] + extra_args
    res = runner.invoke(cli.app, args)
    assert res.exit_code == 0, res.output
    assert "ANSWER(max_tokens=123)" in res.output
    assert retriever_stack_mocks["embed_model"] == expected_model
    assert retriever_stack_mocks["k"] == 2
    assert retriever_stack_mocks["queried_k"] == 2
    assert retriever_stack_mocks["question"] == "How to stop bleeding?"


# -----------------------------
# llm-stream (Retrieval + Streaming)
# -----------------------------
def test_llm_stream_streams_tokens(llm_mocks, retriever_stack_mocks):
    res = runner.invoke(
        cli.app,
        ["llm-stream", "stream this", "--k", "2", "--embed-model", "sbert-x"],
    )
    assert res.exit_code == 0, res.output
    # Tokens der Dummy-LLM-Stream-Ausgabe kommen ohne Newlines
    assert "ABC" in res.output
    assert retriever_stack_mocks["embed_model"] == "sbert-x"
    assert retriever_stack_mocks["k"] == 2
    assert retriever_stack_mocks["queried_k"] == 2
    assert retriever_stack_mocks["question"] == "stream this"


# -----------------------------
# ask-no-retrieval / llm-sanity-no-retrieval
# -----------------------------
def test_ask_no_retrieval_uses_simple_answer(monkeypatch):
    def fake_simple_answer(question, system, config):
        assert "concise, safe training assistant" in system
        assert question == "ping"
        return "pong"

    monkeypatch.setattr(cli, "simple_answer", fake_simple_answer, raising=True)
    res = runner.invoke(cli.app, ["ask-no-retrieval", "ping", "--config", "configs/rag.yaml"])
    assert res.exit_code == 0, res.output
    assert "pong" in res.output


def test_llm_sanity_no_retrieval_alias(monkeypatch):
    monkeypatch.setattr(cli, "simple_answer", lambda *a, **k: "ok", raising=True)
    res = runner.invoke(cli.app, ["llm-sanity-no-retrieval", "whatever"])
    assert res.exit_code == 0, res.output
    assert "ok" in res.output


# -----------------------------
# llm-stream-no-retrieval
# -----------------------------
def test_llm_stream_no_retrieval_streams_tokens(monkeypatch):
    class DummyLLM:
        def __init__(self, cfg):
            self.cfg = cfg
        def make_messages(self, *, user, system):
            assert user == "say hi"
            assert "ERC training assistant" in system
            return [("system", system), ("user", user)]
        def chat_stream(self, msgs):
            for t in ["x", "y"]:
                yield t

    monkeypatch.setattr(cli, "load_llm_config", lambda _: types.SimpleNamespace(max_tokens=1), raising=True)
    monkeypatch.setattr(cli, "LocalLLM", DummyLLM, raising=True)

    res = runner.invoke(cli.app, ["llm-stream-no-retrieval", "say hi"])
    assert res.exit_code == 0, res.output
    assert "xy" in res.output
