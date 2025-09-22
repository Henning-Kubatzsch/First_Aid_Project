# src/rag/interfaces.py
from __future__ import annotations
from typing import Dict, List, Iterable, Optional, Protocol, Any


# Protocol:
# acts as typechecker for chat models
# if you want to implement a new chat model, just make it conform to this protocol

class ChatModel(Protocol):
    """Minimal interface every chat-capable LLM adapter must implement."""

    def make_messages(
        self,
        user: str,
        system: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        ...

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        ...

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Iterable[str]:
        ...


# Already have ChatModel; adding the rest:

class Chunker(Protocol):
    def split(self, text: str, meta: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Return a list of chunks: [{'id': str, 'text': str, 'meta': {...}}]."""
        ...

class Embedder(Protocol):
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Return list of vectors; len == len(texts)."""
        ...
    def embed_one(self, text: str) -> List[float]:
        ...

class VectorIndex(Protocol):
    def build(self, dim: int, space: str = "cosine") -> None: ...
    def upsert(self, vectors: List[List[float]], metas: List[Dict[str, Any]]) -> None: ...
    def query(self, vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Return docs with distances: [{'text': ..., 'meta': {...}, 'score': float}]"""
        ... 
    def save(self, path: str) -> None: ...
    def load(self, path: str) -> None: ...
