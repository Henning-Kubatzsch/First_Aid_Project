# Given a query vector: top-k search (+ optional rerank); returns context items
# TODO: Interface + Abstaction

from __future__ import annotations
from typing import List, Dict, Any
from rag.interfaces import Embedder, VectorIndex

class Retriever:
    def __init__(self, embedder: Embedder, index: VectorIndex, k: int = 5):
        self.embedder = embedder
        self.index = index
        self.k = k

    def search(self, query: str) -> List[Dict[str, Any]]:
        qv = self.embedder.embed_one(query)
        return self.index.query(qv, k=self.k)
