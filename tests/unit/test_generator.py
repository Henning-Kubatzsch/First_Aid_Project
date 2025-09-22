# tests/unit/test_generator.py
import pytest
import rag.generator as g
from rag.generator import (
    LLMConfig,
    load_llm_config,
    family_to_chat_format_and_stops,
    LocalLLM,
    simple_answer,
)

# -------------------------
# Config / mapping basics
# -------------------------

def test_load_llm_config_parses_yaml(tmp_path):
    cfg_path = tmp_path / "cfg.yml"
    cfg_path.write_text(
        "llm:\n"
        f"  model_path: {tmp_path / 'model.gguf'}\n"
        "  family: llama3\n"
        "  stop: [\"<|eot_id|>\"]\n",
        encoding="utf-8",
    )
    cfg = load_llm_config(str(cfg_path))
    assert isinstance(cfg, LLMConfig)
    assert cfg.family == "llama3"
    assert cfg.stop == ["<|eot_id|>"]


@pytest.mark.parametrize(
    "family,expected_format",
    [
        ("qwen", "qwen"),
        ("qwen2", "qwen"),
        ("qwen2.5", "qwen"),
        ("llama3", "llama-3"),
        ("phi3", "phi3"),
        ("mistral", "mistral-instruct"),
        ("unknown", None),
    ],
)
def test_family_mapping_formats(family, expected_format):
    mapping = family_to_chat_format_and_stops(family)
    assert "chat_format" in mapping and "extra_stops" in mapping
    assert mapping["chat_format"] == expected_format
    assert isinstance(mapping["extra_stops"], list)


def test_localllm_init_requires_existing_model_path(tmp_path):
    bad = tmp_path / "missing.gguf"
    with pytest.raises(AssertionError):
        LocalLLM(LLMConfig(model_path=str(bad)))


def test_localllm_init_merges_stops_and_sets_chat_format(tmp_path):
    model_path = tmp_path / "model.gguf"
    model_path.write_bytes(b"")
    cfg = LLMConfig(model_path=str(model_path), family="qwen", stop=["<|endoftext|>", "<CUSTOM>"])
    llm = LocalLLM(cfg)
    assert llm.chat_format == "qwen"
    assert "<|im_end|>" in llm.stop
    assert "<CUSTOM>" in llm.stop
    assert llm.stop.count("<|endoftext|>") == 1


# -------------------------
# Chat (non-stream)
# -------------------------

def test_make_messages_and_chat_uses_defaults(tmp_path, monkeypatch):
    model_path = tmp_path / "m.gguf"
    model_path.write_bytes(b"")
    cfg = LLMConfig(model_path=str(model_path), family="llama3")
    llm = LocalLLM(cfg)

    # deterministic behavior: patch the instance method
    def fake_create_chat_completion(*, messages, **params):
        # sanity: defaults are forwarded
        assert params["stream"] is False
        assert params["temperature"] == cfg.temperature
        assert params["top_p"] == cfg.top_p
        assert params["max_tokens"] == cfg.max_tokens
        return {"choices": [{"message": {"content": "OK"}}]}
    monkeypatch.setattr(llm.llama, "create_chat_completion", fake_create_chat_completion, raising=False)

    msgs = llm.make_messages(user="Hello", system="SYS", history=[{"role": "assistant", "content": "hi"}])
    assert msgs[0] == {"role": "system", "content": "SYS"}
    assert msgs[-1] == {"role": "user", "content": "Hello"}

    out = llm.chat(msgs)
    assert out == "OK"


def test_chat_overrides_params(tmp_path, monkeypatch):
    model_path = tmp_path / "m2.gguf"
    model_path.write_bytes(b"")
    cfg = LLMConfig(model_path=str(model_path), family="phi3", temperature=0.1, top_p=0.5, max_tokens=10)
    llm = LocalLLM(cfg)

    seen = {}
    def fake_create_chat_completion(*, messages, **params):
        seen.update(params)
        return {"choices": [{"message": {"content": "OK"}}]}
    monkeypatch.setattr(llm.llama, "create_chat_completion", fake_create_chat_completion, raising=False)

    msgs = llm.make_messages(user="Hi")
    _ = llm.chat(msgs, temperature=0.9, top_p=0.7, max_tokens=3)

    assert seen["stream"] is False
    assert seen["temperature"] == 0.9
    assert seen["top_p"] == 0.7
    assert seen["max_tokens"] == 3


# -------------------------
# Chat (stream)
# -------------------------

def test_chat_stream_yields_chunks_and_sets_stream_flag(tmp_path, monkeypatch):
    model_path = tmp_path / "m3.gguf"
    model_path.write_bytes(b"")
    cfg = LLMConfig(model_path=str(model_path), family="mistral")
    llm = LocalLLM(cfg)

    def fake_create_chat_completion(*, messages, **params):
        assert params["stream"] is True
        for piece in ["he", "llo"]:
            yield {"choices": [{"delta": {"content": piece}}]}
    monkeypatch.setattr(llm.llama, "create_chat_completion", fake_create_chat_completion, raising=False)

    msgs = llm.make_messages(user="Stream please")
    parts = list(llm.chat_stream(msgs))
    assert "".join(parts) == "hello"


# -------------------------
# simple_answer wiring
# -------------------------

def test_simple_answer_wires_everything(tmp_path, monkeypatch):
    # Patch the module-level class so the ctor uses our dummy instance
    class _LLMStub(LocalLLM):
        def __init__(self, cfg):
            # bypass model file assertion by faking llama handle
            self.cfg = cfg
            self.stop = []
            self.chat_format = "qwen"
            class _Dummy:
                def create_chat_completion(self, *, messages, **params):
                    return {"choices": [{"message": {"content": "OK"}}]}
            self.llama = _Dummy()

    monkeypatch.setattr(g, "LocalLLM", _LLMStub, raising=False)

    cfg_path = tmp_path / "llm.yml"
    # Model path can be non-existent because _LLMStub bypasses the check
    cfg_path.write_text(
        "llm:\n"
        f"  model_path: {tmp_path / 'nonexistent.gguf'}\n"
        "  family: qwen2\n"
        "  max_tokens: 7\n",
        encoding="utf-8",
    )
    ans = simple_answer("Q?", system="S", cfg_path=str(cfg_path))
    assert ans == "OK"
